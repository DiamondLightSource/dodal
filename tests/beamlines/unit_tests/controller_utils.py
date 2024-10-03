from importlib import import_module
from types import ModuleType
from typing import (
    Any,
)

from dodal.aliases import AnyDevice
from dodal.common.beamlines.device_factory import DeviceInitializationController


def make_all_controlled_devices(
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
    initalizers: dict[str, DeviceInitializationController] = (
        _collect_device_initializers(module, include_skipped)
    )
    devices, exceptions = _invoke_device_initalization_controllers(
        initalizers, **kwargs
    )

    return devices, exceptions


def _collect_device_initializers(
    module: ModuleType, include_skipped: bool = False
) -> dict[str, DeviceInitializationController]:
    """Automatically detect device factory functions within a module. They are detected
    via the return type signature e.g. def my_device() -> ADeviceType:

    Args:
        module: The module to inspect
        include_skipped: If True, also load factories with the @skip_device annotation.
        Defaults to False.

    Returns:
        dict[str, AnyDeviceFactory]: Mapping of factory name -> factory.
    """
    initalizers: dict[str, DeviceInitializationController] = {}

    all_variables_in_beamline_file = module.__dict__.values()
    for variable in all_variables_in_beamline_file:
        if isinstance(variable, DeviceInitializationController):
            initalizers[variable._factory.__name__] = variable

    return initalizers


def _invoke_device_initalization_controllers(
    controllers: dict[str, DeviceInitializationController], **kwargs
) -> tuple[dict[str, Any], dict[str, Exception]]:
    """
    Call device factory functions in the correct order to resolve dependencies.

    Args:
        factories: Mapping of function name -> function

    Returns:
        Tuple[dict[str, Any], dict[str, Exception]]: Devices and exceptions encountered.
    """
    devices: dict[str, AnyDevice] = {}
    exceptions: dict[str, Exception] = {}

    # Process all factories until all are either resolved or failed
    for device_name in controllers:
        try:
            controller = controllers[device_name]
            devices[device_name] = controller(**kwargs)
        except Exception as e:
            exceptions[device_name] = e

    return devices, exceptions
