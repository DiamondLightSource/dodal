import inspect
from importlib import import_module
from inspect import signature
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, Type, Union

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


def make_all_devices(module: Union[str, ModuleType, None] = None) -> Dict[str, Any]:
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = collect_factories(module)
    return {device.name: device for device in map(lambda factory: factory(), factories)}


def collect_factories(module: ModuleType) -> Iterable[Callable[..., Any]]:
    for var in module.__dict__.values():
        if callable(var) and is_device_factory(var):
            yield var


def is_device_factory(func: Callable[..., Any]) -> bool:
    return_type = signature(func).return_annotation
    return is_device_type(return_type)


def is_device_type(obj: Type[Any]) -> bool:
    is_class = inspect.isclass(obj)
    follows_protocols = any(
        map(lambda protocol: isinstance(obj, protocol), BLUESKY_PROTOCOLS)
    )
    return is_class and follows_protocols
