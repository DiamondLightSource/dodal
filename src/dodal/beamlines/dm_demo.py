import inspect
import typing
from collections.abc import Callable
from functools import cache, wraps
from types import FunctionType, NoneType
from typing import Annotated, Any, Generic, ParamSpec, TypeVar

from ophyd_async.core import PathProvider
from ophyd_async.epics.adsimdetector import SimDetector
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.devices import motors
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, SkipType

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
        wraps(factory)(self)

    @property
    def name(self) -> str:
        return self.factory.__name__

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

    def __call__(self, *args, **kwargs) -> T:
        return self.factory(*args, **kwargs)  # type: ignore

    def __repr__(self) -> str:
        target = self.factory.__annotations__.get("return")
        target = target.__name__ if target else "???"
        return f"<{self.name}: DeviceFactory -> {target}>"


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
        self,
        *functions: FunctionType,
        fixtures: dict[str, Any] | None = None,
        connect_immediately: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Exception]]:
        """
        Build the devices from the given factories, ensuring that any
        dependencies are built first and passed to later factories as required.
        """
        factories = [self[f.__name__] for f in functions]
        build_list, required_fixtures = self._expand_dependencies(factories)
        fixtures = fixtures or {}
        if missing := required_fixtures - fixtures.keys():
            raise ValueError(f"Missing requirements: {missing}")
        order = self._build_order(
            {dep: self._factories[dep] for dep in build_list}, fixtures=fixtures
        )
        built = {}
        errors = {}
        for device in order:
            deps = self[device].dependencies
            if dep_errs := deps.keys() & errors.keys():
                errors[device] = ValueError(f"Errors building dependencies: {dep_errs}")
            else:
                params = {dep: built.get(dep) or fixtures[dep] for dep in deps}
                try:
                    built[device] = self[device](**params)
                except Exception as e:
                    errors[device] = e
        return (built, errors)

    def __getitem__(self, name):
        return self._factories[name]

    def _expand_dependencies(
        self,
        factories: list[DeviceFactory[Any, Any]],
    ) -> tuple[set[str], set[str]]:  # dependencies, fixtures
        """
        Determine full list of transitive dependencies for the given list and
        any external fixtures that should be provided (aren't available as
        device factories)
        """
        dependencies = set()
        fixtures = set()
        while factories:
            fact = factories.pop()
            dependencies.add(fact.name)
            for dep in fact.dependencies:
                if dep not in dependencies:
                    if dep in self._factories:
                        dependencies.add(dep)
                        factories.append(self[dep])
                    else:
                        fixtures.add(dep)

        return dependencies, fixtures

    def _build_order(
        self, factories: dict[str, DeviceFactory], fixtures=None
    ) -> list[str]:
        """
        Determine the order devices in which devices should be build to ensure
        that dependencies are built before the things that depend on them

        Assumes that all required devices and fixtures are included in the
        given factory list.
        """
        order = []
        available = set(fixtures or {})
        pending = factories
        while pending:
            buffer = {}
            for name, factory in pending.items():
                if factory.skip:
                    continue
                if all(dep in available for dep in factory.dependencies):
                    order.append(name)
                    available.add(name)
                else:
                    buffer[name] = factory
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
    # raise ValueError("Unknown error")
    return "unknown device"


if __name__ == "__main__":
    for name, factory in devices._factories.items():
        print(name, factory, factory.dependencies)
    # print(devices._build_order({"path_provider": ["42"]}))

    # print(devices["stage"])
    # print(devices["unknown"])
    # print(devices.build_all(fixtures={"path_provider": "numtracker"}))
    # print(devices._required_fixtures((devices["base"], devices["base_y"])))
    print(devices._expand_dependencies([devices["base"]]))
    print(devices._expand_dependencies(list(devices._factories.values())))
    # print(devices._build_order({"base": devices["base"]}))

    print(
        devices.build_all(
            base, det, stage, unknown, fixtures={"path_provider": "numtracker"}
        )
    )
