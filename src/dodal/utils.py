import importlib
import inspect
import os
import re
import socket
import string
from collections.abc import Callable, Iterable, Mapping
from importlib import import_module
from inspect import signature
from os import environ
from types import ModuleType
from typing import Any, Protocol, TypeGuard, runtime_checkable

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
from ophyd_async.core import Device as OphydV2Device

import dodal.log
from dodal.aliases import AnyDevice, AnyDeviceFactory, V1DeviceFactory, V2DeviceFactory
from dodal.common.beamlines.controller_utils import make_all_controlled_devices
from dodal.common.beamlines.device_factory import DeviceInitializationController

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


@runtime_checkable
class MovableReadable(Movable, Readable, Protocol): ...


def get_beamline_name(default: str) -> str:
    return environ.get("BEAMLINE") or default


def get_hostname() -> str:
    return socket.gethostname().split(".")[0]


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
        Tuple[dict[str, AnyDevice], dict[str, Exception]]: This represents a tuple containing two dictionaries:

    A dictionary where the keys are device names and the values are devices.
    A dictionary where the keys are device names and the values are exceptions.
    """
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
        if hasattr(module, "CONTROLLED_COLLECTION") and module.CONTROLLED_COLLECTION:
            return make_all_controlled_devices(module, include_skipped, **kwargs)
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
    dependencies: dict[str, set[str]] = {
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

    all_variables_in_beamline_file = module.__dict__.values()
    for variable in all_variables_in_beamline_file:
        if _is_valid_factory(include_skipped, variable) and hasattr(
            variable, "__name__"
        ):
            factories[variable.__name__] = variable
        elif isinstance(variable, DeviceInitializationController):
            factories[variable._factory.__name__] = variable._factory  # noqa: SLF001

    return factories


def _is_valid_factory(include_skipped: bool, var: Any):
    return (
        callable(var)
        and (is_v1_device_factory(var) or is_v2_device_factory(var))
        and (include_skipped or not _is_device_skipped(var))
    )


def _is_device_skipped(func: AnyDeviceFactory) -> bool:
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


def is_new_device_factory(func: Callable) -> TypeGuard[AnyDeviceFactory]:
    try:
        return isinstance(func, DeviceInitializationController)
    except ValueError:
        return False


def is_any_device_factory(func: Callable) -> TypeGuard[AnyDeviceFactory]:
    return (
        is_v1_device_factory(func)
        or is_v2_device_factory(func)
        or is_new_device_factory(func)
    )


def is_v2_device_type(obj: type[Any]) -> bool:
    return inspect.isclass(obj) and isinstance(obj, OphydV2Device)


def is_v1_device_type(obj: type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)
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
