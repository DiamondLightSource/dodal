from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, Union


def make_all_devices(module: Union[str, ModuleType, None] = None) -> Dict[str, Any]:
    if isinstance(module, str) or module is None:
        module = import_module(module or __name__)
    factories = collect_factories(module)
    return {device.name: device for device in map(lambda factory: factory(), factories)}


def collect_factories(module: ModuleType) -> Iterable[Callable[..., Any]]:
    for name, var in module.__dict__.items():
        if name.startswith("make_") and callable(var):
            yield var
