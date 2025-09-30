import asyncio
from concurrent import futures
import concurrent
import inspect
import typing
import warnings
from collections.abc import Callable, Iterable
from functools import cached_property, wraps
from types import NoneType
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Mapping,
    NamedTuple,
    ParamSpec,
    TypeVar,
)

from bluesky.run_engine import (
    RunEngine,
    call_in_bluesky_event_loop,
    get_bluesky_event_loop,
)
from ophyd import Device
from ophyd_async.core import PathProvider
from ophyd_async.epics.adsimdetector import SimDetector
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.devices import motors
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import (
    AnyDevice,
    BeamlinePrefix,
    OphydV1Device,
    OphydV2Device,
    SkipType,
)

BL = "adsim"
DEFAULT_TIMEOUT = 30
PREFIX = BeamlinePrefix("t01")
set_log_beamline(BL)
set_utils_beamline(BL)

T = TypeVar("T")
Args = ParamSpec("Args")


class DeviceFactory(Generic[Args, T]):
    """
    Wrapper around a device factory (any function returning a device) that holds
    a reference to a device manager that can provide dependencies, along with
    default connection information for how the created device should be
    connected.
    """

    factory: Callable[Args, T]
    use_factory_name: bool
    timeout: float
    mock: bool
    _skip: SkipType
    _manager: "DeviceManager"

    def __init__(self, factory, use_factory_name, timeout, mock, skip, manager):
        if any(
            p.kind == inspect.Parameter.POSITIONAL_ONLY
            for p in inspect.signature(factory).parameters.values()
        ):
            raise ValueError(f"{factory.__name__} has positional only arguments")
        self.factory = factory
        self.use_factory_name = use_factory_name
        self.timeout = timeout
        self.mock = mock
        self._skip = skip
        self._manager = manager
        wraps(factory)(self)

    @property
    def name(self) -> str:
        """Name of the underlying factory function"""
        return self.factory.__name__

    @property
    def device_type(self) -> type[T]:
        return inspect.signature(self.factory).return_annotation

    @cached_property
    def dependencies(self) -> set[str]:
        """Names of all parameters"""
        sig = inspect.signature(self.factory)
        return {para.name for para in sig.parameters.values()}

    @cached_property
    def optional_dependencies(self) -> set[str]:
        """Names of optional dependencies"""
        sig = inspect.signature(self.factory)
        return {
            para.name
            for para in sig.parameters.values()
            if para.default is not inspect.Parameter.empty
        }

    @property
    def skip(self) -> bool:
        """
        Whether this device should be skipped as part of build_all - it will
        still be built if a required device depends on it
        """
        return self._skip() if callable(self._skip) else self._skip

    def build(
        self,
        mock: bool = False,
        connect_immediately: bool = False,
        name: str | None = None,
        timeout: float | None = None,
        **fixtures,
    ) -> T:
        """Build this device, building any dependencies first"""
        devices = self._manager.build_devices(
            self,
            fixtures=fixtures,
            mock=mock,
            # connect_immediately=connect_immediately,
            # timeout=timeout or self.timeout,
        )
        if devices.errors:
            raise Exception("??? build")
        else:
            # device = devices[self.name][0]
            if connect_immediately:
                conn = devices.connect(timeout=timeout)
                if conn.connection_errors:
                    raise Exception("??? conn")
            device = devices.devices[self.name][0]
            if name:
                device.set_name(device)
            elif self.use_factory_name:
                device.set_name(self.name)
            return device

    def __call__(self, *args, **kwargs) -> T:
        device = self.factory(*args, **kwargs)
        if isinstance(device, OphydV2Device):
            if self.use_factory_name:
                device.set_name(self.name)
        return device

    def __repr__(self) -> str:
        target = self.factory.__annotations__.get("return")
        target = target.__name__ if target else "???"
        params = inspect.signature(self.factory)
        return f"<{self.name}: DeviceFactory ({params}) -> {target}>"


class ConnectionResult(NamedTuple):
    devices: dict[str, AnyDevice]
    build_errors: dict[str, Exception]
    connection_errors: dict[str, Exception]


class DeviceBuildResult(NamedTuple):
    devices: dict[str, tuple[Any, bool]]
    errors: dict[str, Exception]

    def connect(
        self, timeout: float | None = None, run_engine: RunEngine | None = None
    ) -> ConnectionResult:
        connections = {}
        loop: asyncio.EventLoop = (  # type: ignore
            run_engine.loop if run_engine else get_bluesky_event_loop()
        )
        for name, (device, mock) in self.devices.items():
            fut: futures.Future = asyncio.run_coroutine_threadsafe(
                device.connect(mock=mock, timeout=timeout or 10),  # type: ignore
                loop=loop,
            )
            connections[name] = fut

        connected = {}
        connection_errors = {}
        for name, connection_future in connections.items():
            try:
                connection_future.result(timeout=12)
                connected[name] = self.devices[name][0]
            except Exception as e:
                connection_errors[name] = e

        return ConnectionResult(connected, self.errors, connection_errors)

    # @typing.overload
    # def __getitem__(self, idx: Literal[0]) -> dict[str, Any]: ...
    # @typing.overload
    # def __getitem__(self, idx: Literal[1]) -> dict[str, Exception]: ...

    # def __getitem__(self, idx):
    #     match idx:
    #         case 0:
    #             return {n: d[0] for n, d in self.devices.items()}
    #         case 1:
    #             return self.errors
    #         case _:
    #             raise IndexError()


class DeviceManager:
    _factories: dict[str, DeviceFactory]

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

    def build_all(
        self,
        include_skipped=False,
        fixtures: dict[str, Any] | None = None,
        mock: bool = False,
        # connect_immediately: bool = False,
        # timeout: float | None = None,
    ) -> DeviceBuildResult:
        fixtures = fixtures or {}
        # exclude all skipped devices and those that have been overridden by fixtures
        return self.build_devices(
            *(
                f
                for f in self._factories.values()
                # allow overriding skip but still allow fixtures to override devices
                if (include_skipped or not f.skip) and f.name not in fixtures
            ),
            fixtures=fixtures,
            mock=mock,
            # connect_immediately=connect_immediately,
            # timeout=timeout,
        )

    def build_devices(
        self,
        *factories: DeviceFactory,
        fixtures: dict[str, Any] | None = None,
        mock: bool = False,
        # connect_immediately: bool = False,
        # timeout: float | None = None,
    ) -> DeviceBuildResult:
        """
        Build the devices from the given factories, ensuring that any
        dependencies are built first and passed to later factories as required.
        """
        # TODO: Should we check all the factories are our factories?
        fixtures = fixtures or {}
        if common := fixtures.keys() & {f.name for f in factories}:
            warnings.warn(
                f"Factories ({common}) will be overridden by fixtures", stacklevel=1
            )
            factories = tuple(f for f in factories if f.name not in common)
        if unknown := {f for f in factories if f not in self._factories.values()}:
            raise ValueError(f"Factories ({unknown}) are unknown to this manager")
        build_list = self._expand_dependencies(factories, fixtures)
        order = self._build_order(
            {dep: self._factories[dep] for dep in build_list}, fixtures=fixtures
        )
        built: dict[str, tuple[Any, bool]] = {}
        errors = {}
        for device in order:
            factory = self[device]
            deps = factory.dependencies
            if dep_errs := deps & errors.keys():
                errors[device] = ValueError(f"Errors building dependencies: {dep_errs}")
            else:
                # If we've made it this far, any devices that aren't available must have default
                # values so ignore anything that's missing
                params = {
                    dep: built.get(dep) or fixtures[dep]
                    for dep in deps
                    if dep in built.keys() | fixtures.keys()
                }
                try:
                    built_device = factory(**params)
                    built[device] = (built_device, mock or factory.mock)
                except Exception as e:
                    errors[device] = e

        return DeviceBuildResult(built, errors)

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
            options = fact.optional_dependencies
            for dep in fact.dependencies:
                if dep not in dependencies and dep not in available_fixtures:
                    if dep in self._factories:
                        dependencies.add(dep)
                        factories.append(self[dep])
                    elif dep not in options:
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
                buildable_deps = factory.dependencies & factories.keys()
                # We should only have been called with a resolvable set of things to build
                # but just to double check
                assert buildable_deps.issubset(
                    factory.dependencies - factory.optional_dependencies
                )
                if all(dep in available for dep in buildable_deps):
                    order.append(name)
                    available.add(name)
                else:
                    buffer[name] = factory
            if len(pending) == len(buffer):
                # This should only be reachable if we have circular dependencies
                raise ValueError(
                    f"Cannot determine build order - possibly circular dependencies ({', '.join(pending.keys())})"
                )
            buffer, pending = [], buffer

        return order

    def __repr__(self) -> str:
        return f"<DeviceManager: {len(self._factories)} devices>"


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


@devices.factory(mock=True)
def base(base_x, base_y: motors.Motor) -> Motor:
    # print(base_x)
    # print(base_y)
    return f"{base_x} - {base_y}"


@devices.factory
def base_x() -> motors.Motor:
    # raise ValueError("Not a base_x")
    return "base_x motor"


@devices.factory(skip=True)
def base_y(path_provider) -> motors.Motor:
    # print(f"Using {path_provider=}")
    return "base_y motor"


@devices.factory
def optional(base_x, base_z=42):
    return (base_x, base_z)


@devices.factory
def unknown():
    # raise ValueError("Unknown error")
    return "unknown device"


others = DeviceManager()


@others.factory
def circ_1(circ_2): ...


@others.factory
def circ_2(circ_1): ...


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

    # print(
    #     "build_all",
    #     devices.build_all({"path_provider": "all_nt", "base_y": "other base_y"}),
    # )
    # print(
    #     "build_some",
    #     devices.build_devices(
    #         base, det, stage, unknown, fixtures={"path_provider": "numtracker"}
    #     ),
    # )

    # print("base", optional)
    # print("base_y", base_y)
    # print("b1", b1 := base.build(path_provider="num_track"))
    # print("b2", b2 := base(base_x="base_x motor", base_y="base_y motor"))
    # print("b1 is b2", b1 is b2)

    # print("unknown()", unknown())
    # print("unknown.build()", unknown.build())

    # print("circular", circ_1.build())

    # print("optional deps", optional.dependencies)
    # print("optional optional deps", optional.optional_dependencies)
    # print("optional build", optional.build())
    # print("optional with override", optional.build(base_z=14))
    # print("optional without override", optional(17))
    # print("optional override required", optional.build(base_x=19))

    # valid, errs = devices.build_all(
    #     fixtures={"base_x": 19, "path_provider": "numtrack"}
    # )
    # print(valid)
    # print(errs)

    # valid, errs = devices.build_devices(
    #     base_x, base, optional, fixtures={"base_x": "19", "path_provider": "nt_pp"}
    # )
    # print(valid)
    # print(errs)

    # print(base_x())

    res = devices.build_all(fixtures={"path_provider": "nt_path_provider"})
    print(res)
    conn = res.connect()
    print(conn)

    # devices.build_devices(circ_1, circ_2)
