import functools
import inspect
from collections.abc import Callable
from functools import cache, wraps
from types import NoneType
from typing import Annotated, Any, Generic, ParamSpec, TypeVar
import typing

from ophyd_async.core import PathProvider
from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.devices import motors
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, SkipType
from ophyd_async.epics.motor import Motor

BL = "adsim"
DEFAULT_TIMEOUT = 30
PREFIX = BeamlinePrefix("t01")
set_log_beamline(BL)
set_utils_beamline(BL)

T = TypeVar("T")
Args = ParamSpec("Args")


class DeviceFactory(Generic[Args, T]):
    factory: Callable[Args, T]
    use_factory_name: bool
    timeout: float
    mock: bool
    _skip: SkipType

    def __init__(self, factory, use_factory_name, timeout, mock, skip):
        self.factory = factory
        self.use_factory_name = use_factory_name
        self.timeout = timeout
        self.mock = mock
        self._skip = skip

    @property
    def dependencies(self) -> dict[str, type]:
        sig = inspect.signature(self.factory)
        return {
            para.name: para.annotation
            for para in sig.parameters.values()
            if para.default is inspect.Parameter.empty
        }

    @property
    def skip(self) -> bool:
        return self._skip() if callable(self._skip) else self._skip

    def reset(self):
        self.factory.cache_clear()  # type: ignore

    def __call__(self, **kwargs) -> T:
        return self.factory(**kwargs)

    def __repr__(self) -> str:
        target = self.factory.__annotations__.get("return")
        target = target.__name__ if target else "???"
        return f"<{self.factory.__name__}: DeviceFactory -> {target}>"


class DeviceManager:
    def __init__(self):
        self._factories = {}

    # Overload for using as plain decorator, ie: @devices.factory
    @typing.overload
    def factory(self, func: Callable[Args, T], /) -> Callable[Args, T]: ...

    # Overload for using as configurable decorator, eg: @devices.factory(skip=True)
    @typing.overload
    def factory(
        self,
        func: NoneType = None,
        /,
        use_factory_name: bool = True,
        timeout: float = DEFAULT_TIMEOUT,
        mock: bool = False,
        skip: SkipType = False,
    ) -> Callable[[Callable[Args, T]], Callable[Args, T]]: ...

    def factory(
        self,
        func: Callable[Args, T] | None = None,
        /,
        use_factory_name: Annotated[bool, "Use factory name as name of device"] = True,
        timeout: Annotated[
            float, "Timeout for connecting to the device"
        ] = DEFAULT_TIMEOUT,
        mock: Annotated[bool, "Use Signals with mock backends for device"] = False,
        skip: Annotated[
            SkipType,
            "mark the factory to be (conditionally) skipped when beamline is imported by external program",
        ] = False,
    ) -> Callable[Args, T] | Callable[[Callable[Args, T]], Callable[Args, T]]:
        def decorator(func: Callable[Args, T]) -> Callable[Args, T]:
            factory = cache(func)
            self._factories[func.__name__] = DeviceFactory(
                factory, use_factory_name, timeout, mock, skip
            )
            return factory  # type: ignore

        if func is None:
            return decorator
        return decorator(func)

    def build_all(
        self, fixtures: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Exception]]:
        order = self._build_order(fixtures)
        built = {}
        errors = {}
        for device in order:
            deps = self[device].dependencies
            if deps.keys() & errors.keys():
                errors[device] = ValueError("Errors building dependencies")
            else:
                params = {dep: built.get(dep) or fixtures[dep] for dep in deps}
                try:
                    built[device] = self[device](**params)
                except Exception as e:
                    errors[device] = e
        return (built, errors)

    def __getitem__(self, name):
        return self._factories[name]

    def _build_order(self, fixtures=None) -> list[str]:
        order = []
        available = set(fixtures or {})
        pending = list(self._factories.items())
        while pending:
            buffer = []
            for device in pending:
                if device[1].skip:
                    continue
                if all(dep in available for dep in device[1].dependencies):
                    order.append(device[0])
                    available.add(device[0])
                else:
                    buffer.append(device)
            if len(pending) == len(buffer):
                raise ValueError(f"Cannot fulfil requirements for {pending}")
            buffer, pending = [], buffer

        return order


devices = DeviceManager()


@devices.factory(skip=True, timeout=13, mock=True, use_factory_name=False)
def stage() -> XThetaStage:
    """Build the stage"""
    return XThetaStage(
        f"{PREFIX.beamline_prefix}-MO-SIMC-01:", x_infix="M1", theta_infix="M2"
    )


@devices.factory(skip=True)
def det(path_provider: PathProvider) -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@devices.factory
def base(base_x, base_y: motors.Motor) -> Motor:
    print(base_x)
    print(base_y)
    return base_x + base_y


@devices.factory
def base_x() -> motors.Motor:
    # raise ValueError("Not a base_x")
    return "base_x motor"


@devices.factory
def base_y(path_provider) -> motors.Motor:
    print(f"Using {path_provider=}")
    return "base_y motor"


@devices.factory
def unknown():
    return "unknown device"


if __name__ == "__main__":
    for name, factory in devices._factories.items():
        print(name, factory, factory.dependencies)
    # print(devices._build_order({"path_provider": ["42"]}))

    print(devices["stage"])
    print(devices["unknown"])
    print(devices.build_all(path_provider="numtracker"))
