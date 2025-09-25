import inspect
import typing
from collections.abc import Callable, Iterable
from functools import cache, wraps
from types import NoneType
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
    _manager: "DeviceManager"

    def __init__(self, factory, use_factory_name, timeout, mock, skip, manager):
        self.factory = cache(factory)  # type: ignore
        self.use_factory_name = use_factory_name
        self.timeout = timeout
        self.mock = mock
        self._skip = skip
        self._manager = manager
        wraps(factory)(self)

    @property
    def name(self) -> str:
        return self.factory.__name__

    @property
    def dependencies(self) -> dict[str, type | None]:
        sig = inspect.signature(self.factory)
        return {
            para.name: para.annotation
            if para.annotation is not inspect.Parameter.empty
            else None
            for para in sig.parameters.values()
            # if para.default is inspect.Parameter.empty
        }

    @property
    def skip(self) -> bool:
        return self._skip() if callable(self._skip) else self._skip

    def build(
        self,
        mock: bool = False,
        connect_immediately: bool = False,
        name: str | None = None,
        timeout: float | None = None,
        **fixtures,
    ) -> T:
        devices, errors = self._manager.build_devices(self, fixtures=fixtures)
        if errors:
            raise errors[self.name]
        else:
            return devices[self.name]

    def __call__(self, *args, **kwargs) -> T:
        return self.factory(*args, **kwargs)  # type: ignore

    def __repr__(self) -> str:
        target = self.factory.__annotations__.get("return")
        target = target.__name__ if target else "???"
        return f"<{self.name}: DeviceFactory ({', '.join(self.dependencies.keys())}) -> {target}>"


class DeviceManager:
    def __init__(self):
        self._factories = {}

    # Overload for using as plain decorator, ie: @devices.factory
    @typing.overload
    def factory(self, func: Callable[Args, T], /) -> DeviceFactory[Args, T]: ...

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
    ) -> Callable[[Callable[Args, T]], DeviceFactory[Args, T]]: ...

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
    ) -> DeviceFactory[Args, T] | Callable[[Callable[Args, T]], DeviceFactory[Args, T]]:
        def decorator(func: Callable[Args, T]) -> DeviceFactory[Args, T]:
            factory = DeviceFactory(func, use_factory_name, timeout, mock, skip, self)
            self._factories[func.__name__] = factory
            return factory

        if func is None:
            return decorator
        return decorator(func)

    def build_all(self, fixtures: dict[str, Any] | None = None):
        return self.build_devices(
            *(f for f in self._factories.values() if not f.skip), fixtures=fixtures
        )

    def build_devices(
        self,
        *factories: DeviceFactory,
        fixtures: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Exception]]:
        """
        Build the devices from the given factories, ensuring that any
        dependencies are built first and passed to later factories as required.
        """
        # TODO: Should we check all the factories are our factories?
        print("building: ", factories)
        fixtures = fixtures or {}
        build_list = self._expand_dependencies(factories, fixtures)
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
        factories: Iterable[DeviceFactory[Any, Any]],
        available_fixtures: dict[str, Any],
    ) -> set[str]:
        """
        Determine full list of devices that are required to build the given devices.
        If a dependency is available via the fixtures, a matching device factory
        will not be included unless explicitly requested allowing for devices to
        be overridden.

        Errors:
            If a required dependencies is not available as either a device
            factory or a fixture, a ValueError is raised
        """
        dependencies = set()
        factories = list(factories)
        while factories:
            fact = factories.pop()
            dependencies.add(fact.name)
            for dep in fact.dependencies:
                if dep not in dependencies and dep not in available_fixtures:
                    if dep in self._factories:
                        dependencies.add(dep)
                        factories.append(self[dep])
                    else:
                        raise ValueError(
                            f"Missing fixture or factory for {dep}",
                        )

        return dependencies

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
                # if factory.skip:
                #     continue
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


@devices.factory(skip=stage.skip)
def det(path_provider: PathProvider) -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@devices.factory
def base(base_x, base_y: motors.Motor) -> Motor:
    # print(base_x)
    # print(base_y)
    return base_x + base_y


@devices.factory
def base_x() -> motors.Motor:
    # raise ValueError("Not a base_x")
    return "base_x motor"


@devices.factory(skip=True)
def base_y(path_provider) -> motors.Motor:
    # print(f"Using {path_provider=}")
    return "base_y motor"


@devices.factory
def optional(base_z=42):
    return base_z


@devices.factory
def unknown():
    # raise ValueError("Unknown error")
    return "unknown device"


others = DeviceManager()

if __name__ == "__main__":
    # for name, factory in devices._factories.items():
    #     print(name, factory, factory.dependencies)
    # print(devices._build_order({"path_provider": ["42"]}))

    # print(devices["stage"])
    # print(devices["unknown"])
    # print(devices.build_all(fixtures={"path_provider": "numtracker"}))
    # print(devices._required_fixtures((devices["base"], devices["base_y"])))
    # print(devices._expand_dependencies([devices["base"]]))
    # print(devices._expand_dependencies(list(devices._factories.values())))
    # print(devices._build_order({"base": devices["base"]}))

    print(
        "build_all",
        devices.build_all({"path_provider": "all_nt", "base_y": "other base_y"}),
    )
    print(
        "build_some",
        devices.build_devices(
            base, det, stage, unknown, fixtures={"path_provider": "numtracker"}
        ),
    )

    print("base", base)
    print("base_y", base_y)
    print("b1", b1 := base.build(path_provider="num_track"))
    print("b2", b2 := base(base_x="base_x motor", base_y="base_y motor"))
    print("b1 is b2", b1 is b2)

    print("unknown()", unknown())
    print("unknown.build()", unknown.build())

    print("optional build", optional.build())
    print("optional with override", optional.build(base_z=14))
    print("optional without override", optional())
