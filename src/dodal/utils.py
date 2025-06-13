import functools
import importlib
import inspect
import os
import re
import socket
import string
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from functools import update_wrapper, wraps
from importlib import import_module
from inspect import signature
from os import environ
from types import ModuleType
from typing import (
    Any,
    Generic,
    TypeAlias,
    TypeGuard,
    TypeVar,
)

from bluesky.protocols import (
    Checkable,
    Configurable,
    Flyable,
    HasHints,
    HasName,
    HasParent,
    Movable,
    Pausable,
    Readable,
    Stageable,
    Stoppable,
    Subscribable,
    Triggerable,
    WritesExternalAssets,
)
from bluesky.run_engine import call_in_bluesky_event_loop
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device

import dodal.log

#: Protocols defining interface to hardware
BLUESKY_PROTOCOLS = [
    Checkable,
    Flyable,
    HasHints,
    HasName,
    HasParent,
    Movable,
    Pausable,
    Readable,
    Stageable,
    Stoppable,
    Subscribable,
    WritesExternalAssets,
    Configurable,
    Triggerable,
]

AnyDevice: TypeAlias = OphydV1Device | OphydV2Device
V1DeviceFactory: TypeAlias = Callable[..., OphydV1Device]
V2DeviceFactory: TypeAlias = Callable[..., OphydV2Device]
AnyDeviceFactory: TypeAlias = V1DeviceFactory | V2DeviceFactory


def get_beamline_name(default: str) -> str:
    return environ.get("BEAMLINE") or default


def is_test_mode() -> bool:
    return environ.get("DODAL_TEST_MODE") == "true"


def get_hostname() -> str:
    return socket.gethostname().split(".")[0]


@dataclass
class BeamlinePrefix:
    ixx: str
    suffix: str | None = None

    def __post_init__(self):
        self.suffix = self.ixx[0].upper() if not self.suffix else self.suffix
        self.beamline_prefix = f"BL{self.ixx[1:3]}{self.suffix}"
        self.insertion_prefix = f"SR{self.ixx[1:3]}{self.suffix}"


T = TypeVar("T", bound=AnyDevice)

SkipType = bool | Callable[[], bool]


def skip_device(precondition=lambda: True):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwds) -> T:
            return func(*args, **kwds)

        if precondition():
            wrapper.__skip__ = True  # type: ignore
        return wrapper

    return decorator


class DeviceInitializationController(Generic[T]):
    def __init__(
        self,
        factory: Callable[[], T],
        use_factory_name: bool,
        timeout: float,
        mock: bool,
        skip: SkipType,
    ):
        self._factory: Callable[..., T] = functools.cache(factory)
        self._use_factory_name = use_factory_name
        self._timeout = timeout
        self._mock = mock
        self._skip = skip
        update_wrapper(self, factory)

    @property
    def skip(self) -> bool:
        return self._skip() if callable(self._skip) else self._skip

    def cache_clear(self) -> None:
        """Clears the controller's internal cached instance of the device, if present.
        Noop if not."""

        # Functools adds the cache_clear function via setattr so the type checker
        # does not pick it up.
        self._factory.cache_clear()  # type: ignore

    def __call__(
        self,
        connect_immediately: bool = False,
        name: str | None = None,
        connection_timeout: float | None = None,
        mock: bool | None = None,
        **kwargs,
    ) -> T:
        """Returns an instance of the Device the wrapped factory produces: the same
        instance will be returned if this method is called multiple times, and arguments
        may be passed to override this Controller's configuration.
        Once the device is connected, the value of mock must be consistent, or connect
        must be False.

        Additional keyword arguments will be passed through to the wrapped factory function.

        Args:
            connect_immediately (bool, default False): whether to call connect on the
              device before returning it- connect is idempotent for ophyd-async devices.
              Not connecting to the device allows for the instance to be created prior
              to the RunEngine event loop being configured or for connect to be called
              lazily e.g. by the `ensure_connected` stub.
            name (str | None, optional): an override name to give the device, which is
              also used to name its children. Defaults to None, which does not name the
              device unless the device has no name and this Controller is configured to
              use_factory_name, which propagates the name of the wrapped factory
              function to the device instance.
            connection_timeout (float | None, optional): an override timeout length in
              seconds for the connect method, if it is called. Defaults to None, which
              defers to the timeout configured for this Controller: the default uses
              ophyd_async's DEFAULT_TIMEOUT.
            mock (bool | None, optional): overrides whether to connect to Mock signal
              backends, if connect is called. Defaults to None, which uses the mock
              parameter of this Controller. This value must be used consistently when
              connect is called on the Device.

        Returns:
            T: a singleton instance of the Device class returned by the wrapped factory.

        Raises:
            RuntimeError:   If the device factory was invoked again with different
             keyword arguments, without previously invoking cache_clear()
        """
        is_v2_device = is_v2_device_factory(self._factory)
        is_mock = mock if mock is not None else self._mock
        if is_v2_device:
            device: T = self._factory(**kwargs)
        else:
            device: T = self._factory(mock=is_mock, **kwargs)

        if self._factory.cache_info().currsize > 1:  # type: ignore
            raise RuntimeError(
                f"Device factory method called multiple times with different parameters: "
                f"{self.__name__}"  # type: ignore
            )

        if connect_immediately:
            timeout = (
                connection_timeout if connection_timeout is not None else self._timeout
            )
            if is_v2_device:
                call_in_bluesky_event_loop(
                    device.connect(timeout=timeout, mock=is_mock)
                )
            else:
                assert is_v1_device_type(type(device))
                device.wait_for_connection(timeout=timeout)  # type: ignore

        if name:
            device.set_name(name)
        elif not device.name and self._use_factory_name:
            device.set_name(self._factory.__name__)

        return device


def make_device(
    module: str | ModuleType,
    device_name: str,
    **kwargs,
) -> dict[str, AnyDevice]:
    """Make a single named device and its dependencies from the given beamline module.

    Args:
        module (str | ModuleType): The module to make devices from.
        device_name: Name of the device to construct
        **kwargs: Arguments passed on to every device factory

    Returns:
        dict[str, AnyDevice]: A dict mapping device names to the constructed devices
    """
    if isinstance(module, str):
        module = import_module(module)

    device_collector = {}
    factories = collect_factories(module)
    device_collector[device_name] = _make_one_device(
        module, device_name, device_collector, factories, **kwargs
    )
    return device_collector


def make_all_devices(
    module: str | ModuleType | None = None, include_skipped: bool = False, **kwargs
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    """Makes all devices in the given beamline module.

    In cases of device interdependencies it ensures a device is created before any which
    depend on it.

    Args:
        module (str | ModuleType | None, optional): The module to make devices from.
        **kwargs: Arguments passed on to every device.

    Returns:
        Tuple[Dict[str, AnyDevice], Dict[str, Exception]]: This represents a tuple containing two dictionaries:

    A dictionary where the keys are device names and the values are devices.
    A dictionary where the keys are device names and the values are exceptions.
    """
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = collect_factories(module, include_skipped)
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]] = invoke_factories(
        factories, **kwargs
    )

    return devices


def invoke_factories(
    factories: Mapping[str, AnyDeviceFactory],
    **kwargs,
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    """Call device factory functions in the correct order to resolve dependencies.
    Inspect function signatures to work out dependencies and execute functions in
    correct order.

    If one device takes another as an argument (by name, similar to pytest fixtures)
    this will detect a dependency and create and cache the non-dependant device first.

    Args:
        factories: Mapping of function name -> function

    Returns:
        Tuple[Dict[str, AnyDevice], Dict[str, Exception]]: Tuple of two dictionaries.
        One mapping device name to device, one mapping device name to exception for
        any failed devices
    """

    devices: dict[str, AnyDevice] = {}
    exceptions: dict[str, Exception] = {}

    # Compute tree of dependencies,
    dependencies = {
        factory_name: set(extract_dependencies(factories, factory_name))
        for factory_name in factories.keys()
    }
    while (len(devices) + len(exceptions)) < len(factories):
        leaves = [
            device
            for device, device_dependencies in dependencies.items()
            if (device not in devices and device not in exceptions)
            and len(device_dependencies - set(devices.keys())) == 0
        ]
        dependent_name = leaves.pop()
        params = {name: devices[name] for name in dependencies[dependent_name]}
        try:
            factory = factories[dependent_name]
            if isinstance(factory, DeviceInitializationController):
                # For now we translate the old-style parameters that
                # device_instantiation expects. Once device_instantiation is gone and
                # replaced with DeviceInitializationController we can formalise the
                # API of make_all_devices and make these parameters explicit.
                # https://github.com/DiamondLightSource/dodal/issues/844
                mock = kwargs.get(
                    "mock",
                    kwargs.get(
                        "fake_with_ophyd_sim",
                        False,
                    ),
                )
                connect_immediately = kwargs.get(
                    "connect_immediately",
                    kwargs.get(
                        "wait_for_connection",
                        False,
                    ),
                )
                devices[dependent_name] = factory(
                    mock=mock,
                    connect_immediately=connect_immediately,
                )
            else:
                devices[dependent_name] = factory(**params, **kwargs)
        except Exception as e:
            exceptions[dependent_name] = e

    all_devices = {device.name: device for device in devices.values()}

    return (all_devices, exceptions)


def extract_dependencies(
    factories: Mapping[str, AnyDeviceFactory], factory_name: str
) -> Iterable[str]:
    """Compute dependencies for a device factory. Dependencies are named in the
    factory function signature, similar to pytest fixtures. For example given
    def device_one(): and def device_two(device_one: Readable):, indicate taht
    device_one is a dependency of device_two.

    Args:
        factories: All factories, mapping of function name -> function
        factory_name: The name of the factory in factories whose dependencies need
        computing

    Returns:
        Iterable[str]: Generator of factory names

    Yields:
        Iterator[Iterable[str]]: Factory names
    """

    for name, param in inspect.signature(factories[factory_name]).parameters.items():
        if param.default is inspect.Parameter.empty and name in factories:
            yield name


def collect_factories(
    module: ModuleType, include_skipped: bool = False
) -> dict[str, AnyDeviceFactory]:
    """Automatically detect device factory functions within a module. They are detected
    via the return type signature e.g. def my_device() -> ADeviceType:

    Args:
        module: The module to inspect
        include_skipped: If True, also load factories with the @skip_device annotation.
        Defaults to False.

    Returns:
        dict[str, AnyDeviceFactory]: Mapping of factory name -> factory.
    """

    factories: dict[str, AnyDeviceFactory] = {}

    for var in module.__dict__.values():
        if (
            callable(var)
            and is_any_device_factory(var)
            and (include_skipped or not _is_device_skipped(var))
        ):
            factories[var.__name__] = var
    return factories


def _is_device_skipped(func: AnyDeviceFactory) -> bool:
    if isinstance(func, DeviceInitializationController):
        return func.skip
    return getattr(func, "__skip__", False)


def is_v1_device_factory(func: Callable) -> TypeGuard[V1DeviceFactory]:
    try:
        return_type = signature(func).return_annotation
        return is_v1_device_type(return_type)
    except ValueError:
        return False


def is_v2_device_factory(func: Callable) -> TypeGuard[V2DeviceFactory]:
    try:
        return_type = signature(func).return_annotation
        return is_v2_device_type(return_type)
    except ValueError:
        return False


def is_any_device_factory(func: Callable) -> TypeGuard[AnyDeviceFactory]:
    return is_v1_device_factory(func) or is_v2_device_factory(func)


def is_v2_device_type(obj: type[Any]) -> bool:
    non_parameterized_class = None
    if obj != inspect.Signature.empty:
        if inspect.isclass(obj):
            non_parameterized_class = obj
        elif hasattr(obj, "__origin__"):
            # typing._GenericAlias is the same as types.GenericAlias, maybe?
            # This is all very badly documented and possibly prone to change in future versions of Python
            non_parameterized_class = obj.__origin__
        if non_parameterized_class:
            try:
                return non_parameterized_class and issubclass(
                    non_parameterized_class, OphydV2Device
                )
            except TypeError:
                # Python 3.10 will return inspect.isclass(t) == True but then
                # raise TypeError: issubclass() arg 1 must be a class
                # when inspecting device_factory decorator function itself
                # Later versions of Python seem not to be affected
                pass

    return False


def is_v1_device_type(obj: type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)
    return is_class and follows_protocols and not is_v2_device_type(obj)


def filter_ophyd_devices(
    devices: Mapping[str, AnyDevice],
) -> tuple[Mapping[str, OphydV1Device], Mapping[str, OphydV2Device]]:
    """
    Split a dictionary of ophyd and ophyd-async devices
    (i.e. the output of make_all_devices) into 2 separate dictionaries of the
    different types. Useful when special handling is needed for each type of device.

    Args:
        devices: Dictionary of device name to ophyd or ophyd-async device.

    Raises:
        ValueError: If anything in the dictionary doesn't come from either library.

    Returns:
        Tuple of two dictionaries, one mapping names to ophyd devices and one mapping
        names to ophyd-async devices.
    """

    ophyd_devices = {}
    ophyd_async_devices = {}
    for name, device in devices.items():
        if isinstance(device, OphydV1Device):
            ophyd_devices[name] = device
        elif isinstance(device, OphydV2Device):
            ophyd_async_devices[name] = device
        else:
            raise ValueError(f"{name}: {device} is not an ophyd or ophyd-async device")
    return ophyd_devices, ophyd_async_devices


def get_beamline_based_on_environment_variable() -> ModuleType:
    """
    Gets the dodal module for the current beamline, as specified by the
    BEAMLINE environment variable.
    """
    beamline = get_beamline_name("")

    if beamline == "":
        raise ValueError(
            "Cannot determine beamline - BEAMLINE environment variable not set."
        )

    beamline = beamline.replace("-", "_")
    valid_characters = string.ascii_letters + string.digits + "_"

    if (
        len(beamline) == 0
        or beamline[0] not in string.ascii_letters
        or any(c not in valid_characters for c in beamline)
    ):
        raise ValueError(
            f"Invalid BEAMLINE variable - module name is not a permissible python module name, got '{beamline}'"
        )

    try:
        return importlib.import_module(f"dodal.beamlines.{beamline}")
    except ImportError as e:
        raise ValueError(
            f"Failed to import beamline-specific dodal module 'dodal.beamlines.{beamline}'."
            " Ensure your BEAMLINE environment variable is set to a known instrument."
        ) from e


def _find_next_run_number_from_files(file_names: list[str]) -> int:
    valid_numbers = []

    for file_name in file_names:
        file_name = file_name.strip(".nxs")
        # Give warning if nexus file name isn't in expcted format, xxx_number.nxs
        match = re.search(r"_\d+$", file_name)
        if match is not None:
            valid_numbers.append(int(re.findall(r"\d+", file_name)[-1]))
        else:
            dodal.log.LOGGER.warning(
                f"Identified nexus file {file_name} with unexpected format"
            )
    return max(valid_numbers) + 1 if valid_numbers else 1


def get_run_number(directory: str, prefix: str = "") -> int:
    """Looks at the numbers coming from all nexus files with the format
    "{prefix}_(any number}.nxs", and returns the highest number + 1, or 1 if there are
    no matching numbers found. If no prefix is given, considers all files in the dir."""
    nexus_file_names = [
        file
        for file in os.listdir(directory)
        if file.endswith(".nxs") and file.startswith(prefix)
    ]

    if len(nexus_file_names) == 0:
        return 1
    else:
        return _find_next_run_number_from_files(nexus_file_names)


def _make_one_device(
    module: ModuleType,
    device_name: str,
    devices: dict[str, AnyDevice],
    factories: dict[str, AnyDeviceFactory],
    **kwargs,
) -> AnyDevice:
    factory = factories.get(device_name)
    if not factory:
        raise ValueError(f"Unable to find factory for {device_name}")

    dependencies = list(extract_dependencies(factories, device_name))
    for dependency_name in dependencies:
        if dependency_name not in devices:
            try:
                devices[dependency_name] = _make_one_device(
                    module, dependency_name, devices, factories, **kwargs
                )
            except Exception as e:
                raise RuntimeError(
                    f"Unable to construct device {dependency_name}"
                ) from e

    params = {name: devices[name] for name in dependencies}
    return factory(**params, **kwargs)
