import importlib
import inspect
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
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device

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

AnyDevice: TypeAlias = Union[OphydV1Device, OphydV2Device]
V1DeviceFactory: TypeAlias = Callable[..., OphydV1Device]
V2DeviceFactory: TypeAlias = Callable[..., OphydV2Device]
AnyDeviceFactory: TypeAlias = Union[V1DeviceFactory, V2DeviceFactory]


def get_beamline_name(default: str) -> str:
    return environ.get("BEAMLINE") or default


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
    module: Union[str, ModuleType, None] = None, **kwargs
) -> Dict[str, AnyDevice]:
    """Makes all devices in the given beamline module.

    In cases of device interdependencies it ensures a device is created before any which
    depend on it.

    Args:
        module (Union[str, ModuleType, None], optional): The module to make devices from.
        **kwargs: Arguments passed on to every device.

    Returns:
        Dict[str, Any]: A dictionary of device name and device
    """
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = collect_factories(module)
    devices: dict[str, AnyDevice] = invoke_factories(factories, **kwargs)

    return devices


def invoke_factories(
    factories: Mapping[str, AnyDeviceFactory],
    **kwargs,
) -> Dict[str, AnyDevice]:
    devices: dict[str, AnyDevice] = {}

    dependencies = {
        factory_name: set(extract_dependencies(factories, factory_name))
        for factory_name in factories.keys()
    }

    while len(devices) < len(factories):
        leaves = [
            device
            for device, device_dependencies in dependencies.items()
            if device not in devices.keys()
            and len(device_dependencies - set(devices.keys())) == 0
        ]
        dependent_name = leaves.pop()
        params = {name: devices[name] for name in dependencies[dependent_name]}
        devices[dependent_name] = factories[dependent_name](**params, **kwargs)

    all_devices = {device.name: device for device in devices.values()}

    return all_devices


def extract_dependencies(
    factories: Mapping[str, AnyDeviceFactory], factory_name: str
) -> Iterable[str]:
    for name, param in inspect.signature(factories[factory_name]).parameters.items():
        if param.default is inspect.Parameter.empty and name in factories:
            yield name


def collect_factories(module: ModuleType) -> dict[str, AnyDeviceFactory]:
    factories: dict[str, AnyDeviceFactory] = {}

    for var in module.__dict__.values():
        if callable(var) and is_any_device_factory(var) and not _is_device_skipped(var):
            factories[var.__name__] = var

    return factories


def _is_device_skipped(func: AnyDeviceFactory) -> bool:
    if not hasattr(func, "__skip__"):
        return False
    return func.__skip__  # type: ignore


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
        or not all(c in valid_characters for c in beamline)
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
