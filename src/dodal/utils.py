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
) -> Dict[str, HasName]:
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
    return invoke_factories(factories)


def invoke_factories(
    factories: Mapping[str, Callable[..., Any]],
    **kwargs,
) -> Dict[str, HasName]:
    devices: Dict[str, Any] = {}
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
    factories: Mapping[str, Callable[..., Any]], factory_name: str
) -> Iterable[str]:
    for name, param in inspect.signature(factories[factory_name]).parameters.items():
        if param.default is inspect.Parameter.empty and name in factories:
            yield name


def collect_factories(module: ModuleType) -> Mapping[str, Callable[..., Any]]:
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
    return_type = signature(func).return_annotation
    return _is_device_type(return_type)


def _is_device_type(obj: Type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(
        map(lambda protocol: isinstance(obj, protocol), BLUESKY_PROTOCOLS)
    )
    return is_class and follows_protocols
