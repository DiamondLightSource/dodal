import asyncio
import inspect
import itertools
import typing
import warnings
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from functools import cached_property, wraps
from inspect import Parameter
from types import NoneType
from typing import (
    Annotated,
    Any,
    Concatenate,
    Generic,
    NamedTuple,
    ParamSpec,
    Self,
    TypeVar,
)

from bluesky.run_engine import (
    get_bluesky_event_loop,
)
from ophyd.sim import make_fake_device

from dodal.common.beamlines.beamline_utils import (
    wait_for_connection,
)
from dodal.utils import (
    AnyDevice,
    OphydV1Device,
    OphydV2Device,
    SkipType,
)

DEFAULT_TIMEOUT = 30

T = TypeVar("T")
Args = ParamSpec("Args")

V1 = TypeVar("V1", bound=OphydV1Device)
V2 = TypeVar("V2", bound=OphydV2Device)

DeviceFactoryDecorator = Callable[[Callable[Args, V2]], "DeviceFactory[Args, V2]"]
OphydInitialiser = Callable[Concatenate[V1, ...], V1 | None]

_EMPTY = object()
"""Sentinel value to distinguish between missing values and present but null values"""


class LazyFixtures(Mapping[str, Any]):
    """
    Wrapper around fixtures and fixture generators

    If a fixture is provided at runtime, the generator function does not have to be called.
    """

    ready: MutableMapping[str, Any]
    lazy: MutableMapping[str, Callable[[], Any]]

    def __init__(
        self,
        provided: Mapping[str, Any] | None,
        factories: Mapping[str, Callable[[], Any]],
    ):
        # wrap to prevent modification escaping
        self.ready = dict(provided or {})
        # drop duplicate keys so the len and iter methods are easier
        self.lazy = {k: v for k, v in factories.items() if k not in self.ready}

    def __contains__(self, key: Any) -> bool:
        return key in self.ready or key in self.lazy

    def __len__(self) -> int:
        # Can just add the lengths as the keys are distinct by construction
        return len(self.ready.keys()) + len(self.lazy.keys())

    def __getitem__(self, key: str) -> Any:
        if (value := self.ready.get(key, _EMPTY)) is not _EMPTY:
            return value
        if factory := self.lazy.pop(key, None):
            value = factory()
            self.ready[key] = value
            return value
        raise KeyError(key)

    def __iter__(self):
        return itertools.chain(self.lazy.keys(), self.ready.keys())


class DeviceFactory(Generic[Args, V2]):
    """
    Wrapper around a device factory (any function returning a device) that holds
    a reference to a device manager that can provide dependencies, along with
    default connection information for how the created device should be
    connected.
    """

    factory: Callable[Args, V2]
    use_factory_name: bool
    timeout: float
    mock: bool
    _skip: SkipType
    _manager: "DeviceManager"

    def __init__(self, factory, use_factory_name, timeout, mock, skip, manager):
        if any(
            p.kind == Parameter.POSITIONAL_ONLY
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
    def device_type(self) -> type[V2]:
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
            if para.default is not Parameter.empty
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
    ) -> V2:
        """Build this device, building any dependencies first"""
        devices = self._manager.build_devices(
            self,
            fixtures=fixtures,
            mock=mock,
        )
        if devices.errors:
            # TODO: NotBuilt?
            raise Exception("??? build")
        else:
            if connect_immediately:
                conn = devices.connect(timeout=timeout or self.timeout)
                if conn.connection_errors:
                    # TODO: NotConnected?
                    raise Exception("??? conn")
            device = devices.devices[self.name].device
            if name:
                device.set_name(name)
            return device  # type: ignore - it's us, honest

    def _create(self, *args, **kwargs) -> V2:
        return self(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> V2:
        device = self.factory(*args, **kwargs)
        device.set_name(self.name)
        return device

    def __repr__(self) -> str:
        target = self.factory.__annotations__.get("return")
        target = target.__name__ if target else "???"
        params = inspect.signature(self.factory)
        return f"<{self.name}: DeviceFactory ({params}) -> {target}>"


class V1DeviceFactory(Generic[V1]):
    """
    Wrapper around an ophyd v1 device that holds a reference to a device
    manager that can provide dependencies, along with default connection
    information for how the created device should be connected.
    """

    def __init__(
        self,
        *,
        factory: type[V1],
        prefix: str,
        mock: bool,
        skip: SkipType,
        wait: bool,
        timeout: int,
        init: OphydInitialiser[V1] | None,
        manager: "DeviceManager",
    ):
        self.factory = factory
        self.prefix = prefix
        self.mock = mock
        self._skip = skip
        self.wait = wait
        self.timeout = timeout
        self.post_create = init or (lambda x: x)
        self._manager = manager
        if init:
            wraps(init)(self)

    @property
    def name(self) -> str:
        """Name of the underlying factory function"""
        return self.post_create.__name__

    @property
    def device_type(self) -> type[V1]:
        return self.factory

    @cached_property
    def dependencies(self) -> set[str]:
        """Names of all parameters"""
        sig = inspect.signature(self.post_create)
        # first parameter should be the device we've just built
        _, *params = sig.parameters.values()
        return {para.name for para in params}

    @cached_property
    def optional_dependencies(self) -> set[str]:
        """Names of optional dependencies"""
        sig = inspect.signature(self.post_create)
        _, *params = sig.parameters.values()
        return {para.name for para in params if para.default is not Parameter.empty}

    @property
    def skip(self) -> bool:
        """
        Whether this device should be skipped as part of build_all - it will
        still be built if a required device depends on it
        """
        return self._skip() if callable(self._skip) else self._skip

    def mock_if_needed(self, mock=False) -> Self:
        # TODO: Remove when Ophyd V1 support is no longer required
        factory = (
            make_fake_device(self.factory) if (self.mock or mock) else self.factory
        )
        return self.__class__(
            factory=factory,
            prefix=self.prefix,
            mock=mock or self.mock,
            skip=self._skip,
            wait=self.wait,
            timeout=self.timeout,
            init=self.post_create,
            manager=self._manager,
        )

    def __call__(self, *args, **kwargs):
        """Call the wrapped function to make decorator transparent"""
        return self.post_create(*args, **kwargs)

    def _create(self, *args, **kwargs) -> V1:
        device = self.factory(name=self.name, prefix=self.prefix)
        if self.wait:
            wait_for_connection(device, timeout=self.timeout)
        self.post_create(device, *args, **kwargs)
        return device

    def build(self, mock: bool = False, fixtures: dict[str, Any] | None = None) -> V1:
        """Build this device, building any dependencies first"""
        devices = self._manager.build_devices(
            self,
            fixtures=fixtures,
            mock=mock,
        ).or_raise()

        device = devices.devices[self.name].device
        return device  # type: ignore - it's us really, promise


class ConnectionSpec(NamedTuple):
    """A device paired with the options used to configure it"""

    device: OphydV2Device
    mock: bool
    timeout: float


class ConnectionResult(NamedTuple):
    """Wrapper around results of building and connecting devices"""

    devices: dict[str, AnyDevice]
    build_errors: dict[str, Exception]
    connection_errors: dict[str, Exception]

    def or_raise(self) -> dict[str, Any]:
        """Re-raise any errors from build or connect stage or return devices"""
        if self.build_errors or self.connection_errors:
            all_exc = []
            for name, exc in (self.build_errors | self.connection_errors).items():
                exc.add_note(name)
                all_exc.append(exc)
            raise ExceptionGroup("Some devices failed", tuple(all_exc))
        return self.devices


class DeviceBuildResult(NamedTuple):
    """Wrapper around the results of building devices"""

    devices: dict[str, ConnectionSpec]
    errors: dict[str, Exception]

    def connect(self, timeout: float | None = None) -> ConnectionResult:
        """Connect all devices that didn't fail to build"""
        connections = {}
        connected = {}
        loop: asyncio.EventLoop = get_bluesky_event_loop()  # type: ignore
        for name, (device, mock, dev_timeout) in self.devices.items():
            if not isinstance(device, OphydV2Device):
                connected[name] = device
                continue
            timeout = timeout or dev_timeout or DEFAULT_TIMEOUT
            fut = asyncio.run_coroutine_threadsafe(
                device.connect(mock=mock, timeout=timeout),
                loop=loop,
            )
            connections[name] = fut

        connection_errors = {}
        for name, connection_future in connections.items():
            try:
                connection_future.result()
                connected[name] = self.devices[name].device
            except Exception as e:
                connection_errors[name] = e

        return ConnectionResult(connected, self.errors, connection_errors)

    def or_raise(self) -> Self:
        """Re-raise any build errors"""
        if self.errors:
            for name, exc in self.errors.items():
                exc.add_note(name)
            raise ExceptionGroup("Some devices failed", tuple(self.errors.values()))
        return self


class DeviceManager:
    """Manager to handle building and connecting interdependent devices"""

    _factories: dict[str, DeviceFactory]
    _fixtures: dict[str, Callable[[], Any]]
    _v1_factories: dict[str, V1DeviceFactory]

    def __init__(self):
        self._factories = {}
        self._v1_factories = {}
        self._fixtures = {}

    def fixture(self, func: Callable[[], T]) -> Callable[[], T]:
        """Add a function that can provide fixtures required by the factories"""
        self._fixtures[func.__name__] = func
        return func

    def v1_init(
        self,
        factory: type[V1],
        prefix: str,
        mock: bool = False,
        skip: SkipType = False,
        wait: bool = False,
    ):
        def decorator(init: OphydInitialiser[V1]):
            name = init.__name__
            if name in self:
                raise ValueError(f"Duplicate factory name: {name}")
            device_factory = V1DeviceFactory(
                factory=factory,
                prefix=prefix,
                mock=mock,
                skip=skip,
                wait=wait,
                timeout=DEFAULT_TIMEOUT,
                init=init,
                manager=self,
            )
            self._v1_factories[name] = device_factory
            return device_factory

        return decorator

    # Overload for using as plain decorator, ie: @devices.factory
    @typing.overload
    def factory(self, func: Callable[Args, V2], /) -> DeviceFactory[Args, V2]: ...

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
    ) -> Callable[[Callable[Args, V2]], DeviceFactory[Args, V2]]: ...

    def factory(
        self,
        func: Callable[Args, V2] | None = None,
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
    ) -> DeviceFactory[Args, V2] | DeviceFactoryDecorator[Args, V2]:
        def decorator(func: Callable[Args, V2]) -> DeviceFactory[Args, V2]:
            if func.__name__ in self:
                raise ValueError(f"Duplicate factory name: {func.__name__}")
            factory = DeviceFactory(func, use_factory_name, timeout, mock, skip, self)
            self._factories[func.__name__] = factory
            return factory

        if func is None:
            return decorator
        return decorator(func)

    def build_and_connect(
        self,
        *,
        fixtures: dict[str, Any] | None = None,
        mock: bool = False,
        timeout: float | None = None,
    ) -> ConnectionResult:
        return self.build_all(fixtures=fixtures, mock=mock).connect(timeout=timeout)

    def build_all(
        self,
        include_skipped=False,
        fixtures: dict[str, Any] | None = None,
        mock: bool = False,
    ) -> DeviceBuildResult:
        # exclude all skipped devices and those that have been overridden by fixtures

        return self.build_devices(
            *(
                f
                for f in (self._factories | self._v1_factories).values()
                # allow overriding skip but still allow fixtures to override devices
                if (include_skipped or not f.skip)
                # don't build anything that has been overridden by a fixture
                and (not fixtures or f.name not in fixtures)
            ),
            fixtures=fixtures,
            mock=mock,
        )

    def build_devices(
        self,
        *factories: DeviceFactory | V1DeviceFactory,
        fixtures: Mapping[str, Any] | None = None,
        mock: bool = False,
    ) -> DeviceBuildResult:
        """
        Build the devices from the given factories, ensuring that any
        dependencies are built first and passed to later factories as required.
        """

        fixtures = LazyFixtures(provided=fixtures, factories=self._fixtures)
        if common := fixtures.keys() & {f.name for f in factories}:
            warnings.warn(
                f"Factories ({common}) will be overridden by fixtures", stacklevel=1
            )
            factories = tuple(f for f in factories if f.name not in common)
        build_list = self._expand_dependencies(factories, fixtures)
        order = self._build_order(
            {dep: self[dep] for dep in build_list}, fixtures=fixtures
        )
        built: dict[str, ConnectionSpec] = {}
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
                    dep: value
                    for dep in deps
                    # get from built if it's there, from fixtures otherwise...
                    if (value := (built.get(dep, fixtures.get(dep, _EMPTY))))
                    # ...and skip if in neither
                    is not _EMPTY
                }
                try:
                    if isinstance(factory, V1DeviceFactory):
                        factory = factory.mock_if_needed(mock)
                    built_device = factory._create(**params)
                    built[device] = ConnectionSpec(
                        built_device,
                        mock=mock or factory.mock,
                        timeout=factory.timeout,
                    )
                except Exception as e:
                    errors[device] = e

        return DeviceBuildResult(built, errors)

    def __contains__(self, name):
        return name in self._factories or name in self._v1_factories

    def __getitem__(self, name):
        return self._factories.get(name) or self._v1_factories[name]

    def _expand_dependencies(
        self,
        factories: Iterable[DeviceFactory[..., V2] | V1DeviceFactory[V1]],
        available_fixtures: Mapping[str, Any],
    ) -> set[str]:
        """
        Determine full list of devices that are required to build the given devices.
        If a dependency is available via the fixtures, a matching device factory
        will not be included unless explicitly requested allowing for devices to
        be overridden.

        Errors:
            If a required dependency is not available as either a device
            factory or a fixture, a ValueError is raised
        """
        dependencies = set()
        factories = set(factories)
        while factories:
            fact = factories.pop()
            dependencies.add(fact.name)
            options = fact.optional_dependencies
            for dep in fact.dependencies:
                if dep not in dependencies and dep not in available_fixtures:
                    if dep in self._factories:
                        factories.add(self[dep])
                    elif dep not in options:
                        raise ValueError(
                            f"Missing fixture or factory for {dep}",
                        )

        return dependencies

    def _build_order(
        self,
        factories: dict[str, DeviceFactory[..., V2] | V1DeviceFactory[V1]],
        fixtures: Mapping[str, Any],
    ) -> list[str]:
        """
        Determine the order devices in which devices should be build to ensure
        that dependencies are built before the things that depend on them

        Assumes that all required devices and fixtures are included in the
        given factory list.
        """

        # TODO: This is not an efficient way of doing this
        # However, for realistic use cases, it is fast enough for now
        order = []
        available = set(fixtures.keys())
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
