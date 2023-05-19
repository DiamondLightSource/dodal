import inspect
import socket
from collections import namedtuple
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
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
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
from ophyd.utils import ExceptionBundle

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

DeviceDict = Dict[str, HasName]


class DependentDeviceInstantiationException(Exception):
    """One or more exceptions was raised while instantiating devices this device depends on"""

    def __init__(self, exceptions: Mapping[str, Exception]):
        self.exceptions = exceptions


@dataclass
class ExceptionInformation:
    exception: Exception
    return_type: type


@dataclass
class DevicesAndExceptions:
    devices: DeviceDict
    exceptions: Dict[str, ExceptionInformation]


Point2D = namedtuple("Point2D", ["x", "y"])
Point3D = namedtuple("Point3D", ["x", "y", "z"])

T = TypeVar("T")


def get_beamline_name(ixx: str) -> str:
    bl = environ.get("BEAMLINE")
    if bl is None:
        return f"s{ixx[1:]}"
    else:
        return bl


def get_hostname() -> str:
    return socket.gethostname().split(".")[0]


@dataclass
class BeamlinePrefix:
    ixx: str
    suffix: Optional[str] = None

    def __post_init__(self):
        self.suffix = self.ixx[0].upper() if not self.suffix else self.suffix
        self.beamline_prefix = f"BL{self.ixx[1:3]}{self.suffix}"
        self.insertion_prefix = f"SR{self.ixx[1:3]}{self.suffix}"


def skip_device(precondition=lambda: True):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwds) -> T:
            return func(*args, **kwds)

        if precondition:
            wrapper.__skip__ = True  # type: ignore
        return wrapper

    return decorator


def make_all_devices(
    module: Union[str, ModuleType, None] = None, **kwargs
) -> DeviceDict:
    """Makes all devices in the given beamline module.

    In cases of device interdependencies it ensures a device is created before any which
    depend on it.

    Args:
        module (Union[str, ModuleType, None], optional): The module to make devices from.
        **kwargs: Arguments passed on to every device.

    Returns:
        Dict[str, Any]: A dictionary of device name and device
    """
    devices_and_exceptions = make_all_devices_without_throwing(module, **kwargs)
    if devices_and_exceptions.exceptions:
        if len(devices_and_exceptions.exceptions) == 1:
            raise devices_and_exceptions.exceptions.popitem()[1].exception
        raise ExceptionBundle(
            msg=f"Exceptions while executing device factories: {list(devices_and_exceptions.exceptions.keys())}",
            exceptions=devices_and_exceptions.exceptions,
        )
    return devices_and_exceptions.devices


def make_all_devices_without_throwing(
    module: Union[str, ModuleType, None] = None, **kwargs
) -> DevicesAndExceptions:
    """Makes all devices in the given beamline module.

    In cases of device interdependencies it ensures a device is created before any which
    depend on it.
    In cases of devices failing to instantiate, a reference to the device with the
    exception is stored to allow other devices to instantiate.
    If a failing device is a dependency of other devices, the dependent devices do not
    attempt to instantiate.

    Args:
        module (Union[str, ModuleType, None], optional): The module to make devices from.
        **kwargs: Arguments passed on to every device.

    Returns:
        Dict[str, Any]: A dictionary of device name and device
    """
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = _collect_factories(module)
    return _invoke_factories(factories, **kwargs)


def _invoke_factories(
    factories: Mapping[str, Callable[..., Any]],
    **kwargs,
) -> DevicesAndExceptions:
    devices: Dict[str, HasName] = {}
    exceptions: Dict[str, ExceptionInformation] = {}
    dependencies = {
        factory_name: set(_extract_dependencies(factories, factory_name))
        for factory_name in factories.keys()
    }
    while len(devices) + len(exceptions) < len(factories):
        leaves = [
            device
            for device, device_dependencies in dependencies.items()
            if device not in devices
            and device not in exceptions
            and all(
                dependency in devices or dependency in exceptions
                for dependency in device_dependencies
            )
        ]
        dependent_name = leaves.pop()
        factory = factories[dependent_name]
        return_type = signature(factory).return_annotation
        failed_dependencies = {
            name: exception.exception
            for name, exception in exceptions.items()
            if name in dependencies[dependent_name]
        }
        if failed_dependencies:
            exceptions[dependent_name] = ExceptionInformation(
                return_type=return_type,
                exception=DependentDeviceInstantiationException(
                    exceptions=failed_dependencies,
                ),
            )
        else:
            try:
                params = {
                    name: devices[name]
                    for name in dependencies[dependent_name]
                    if name in devices
                }
                devices[dependent_name] = factory(**params, **kwargs)
            except Exception as e:
                exceptions[dependent_name] = ExceptionInformation(
                    return_type=return_type, exception=e
                )

    all_devices = {device.name: device for device in devices.values()}

    return DevicesAndExceptions(all_devices, exceptions)


def _extract_dependencies(
    factories: Mapping[str, Callable[..., Any]], factory_name: str
) -> Iterable[str]:
    for name, param in inspect.signature(factories[factory_name]).parameters.items():
        if param.default is inspect.Parameter.empty and name in factories:
            yield name


def _collect_factories(module: ModuleType) -> Mapping[str, Callable[..., Any]]:
    factories = {}
    for var in module.__dict__.values():
        if callable(var) and _is_device_factory(var) and not _is_device_skipped(var):
            factories[var.__name__] = var
    return factories


def _is_device_skipped(func: Callable[..., Any]) -> bool:
    if not hasattr(func, "__skip__"):
        return False
    return func.__skip__  # type: ignore


def _is_device_factory(func: Callable[..., Any]) -> bool:
    try:
        return_type = signature(func).return_annotation
        return _is_device_type(return_type)
    except ValueError:  # e.g. built ins without a signature
        return False


def _is_device_type(obj: Type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(
        map(lambda protocol: isinstance(obj, protocol), BLUESKY_PROTOCOLS)
    )
    return is_class and follows_protocols
