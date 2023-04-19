import inspect
import socket
import numpy as np
from collections import namedtuple
from dataclasses import dataclass
from functools import wraps
from importlib import import_module
from inspect import signature
from os import environ
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, Optional, Type, Union

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

def create_point(*args):
    args = list(args)
    for index, arg in enumerate(args):
        if args[index] is None:
            args[index] = 0
    
    if len(args) == 2:
        return np.array([args[0], args[1]], dtype=np.float16)
    elif len(args) == 3:
        return np.array([args[0], args[1], args[2]], dtype=np.float16)
    else:
        raise TypeError("Invalid number of arguments")


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
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args, **kwds):
            return func(*args, **kwds)

        if precondition:
            wrapper.__skip__ = True  # type: ignore
        return wrapper

    return decorator


def make_all_devices(
    module: Union[str, ModuleType, None] = None, **kwargs
) -> Dict[str, Any]:
    """Makes all devices in the given beamline module.

    Args:
        module (Union[str, ModuleType, None], optional): The module to make devices from.
        **kwargs: Arguments passed on to every device.

    Returns:
        Dict[str, Any]: A dictionary of device name and device
    """
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = collect_factories(module)
    return {
        device.name: device
        for device in map(lambda factory: factory(**kwargs), factories)
    }


def collect_factories(module: ModuleType) -> Iterable[Callable[..., Any]]:
    for var in module.__dict__.values():
        if callable(var) and _is_device_factory(var) and not _is_device_skipped(var):
            yield var


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
