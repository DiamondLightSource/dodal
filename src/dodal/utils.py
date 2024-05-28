import importlib
import inspect
import os
import re
import socket
import string
from dataclasses import dataclass
from functools import wraps
from importlib import import_module
from inspect import signature
from os import environ
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Tuple,
    Type,
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
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device

import dodal.log

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias


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


def skip_device(precondition=lambda: True):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwds) -> T:
            return func(*args, **kwds)

        if precondition():
            wrapper.__skip__ = True  # type: ignore
        return wrapper

    return decorator


def make_all_devices(
    module: str | ModuleType | None = None, include_skipped: bool = False, **kwargs
) -> Tuple[Dict[str, AnyDevice], Dict[str, Exception]]:
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
    devices: Tuple[Dict[str, AnyDevice], Dict[str, Exception]] = invoke_factories(
        factories, **kwargs
    )

    return devices


def invoke_factories(
    factories: Mapping[str, AnyDeviceFactory],
    **kwargs,
) -> Tuple[Dict[str, AnyDevice], Dict[str, Exception]]:
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
            devices[dependent_name] = factories[dependent_name](**params, **kwargs)
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
    return getattr(func, "__skip__", False)


def is_v1_device_factory(func: Callable) -> bool:
    try:
        return_type = signature(func).return_annotation
        return is_v1_device_type(return_type)
    except ValueError:
        return False


def is_v2_device_factory(func: Callable) -> bool:
    try:
        return_type = signature(func).return_annotation
        return is_v2_device_type(return_type)
    except ValueError:
        return False


def is_any_device_factory(func: Callable) -> bool:
    return is_v1_device_factory(func) or is_v2_device_factory(func)


def is_v2_device_type(obj: Type[Any]) -> bool:
    return inspect.isclass(obj) and issubclass(obj, OphydV2Device)


def is_v1_device_type(obj: Type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(
        (isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)
    )
    return is_class and follows_protocols and not is_v2_device_type(obj)


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
            "Invalid BEAMLINE variable - module name is not a permissible python module name, got '{}'".format(
                beamline
            )
        )

    try:
        return importlib.import_module("dodal.beamlines.{}".format(beamline))
    except ImportError as e:
        raise ValueError(
            f"Failed to import beamline-specific dodal module 'dodal.beamlines.{beamline}'."
            " Ensure your BEAMLINE environment variable is set to a known instrument."
        ) from e


def _find_next_run_number_from_files(file_names: List[str]) -> int:
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


def get_run_number(directory: str) -> int:
    """Looks at the numbers coming from all nexus files with the format "xxx_(any number}.nxs", and returns the highest number + 1,
    or 1 if there are no numbers found"""
    nexus_file_names = [file for file in os.listdir(directory) if file.endswith(".nxs")]

    if len(nexus_file_names) == 0:
        return 1
    else:
        return _find_next_run_number_from_files(nexus_file_names)
