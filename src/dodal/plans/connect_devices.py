from collections.abc import Callable, Collection, Mapping, Sequence
from typing import ParamSpec

from bluesky.utils import MsgGenerator, make_decorator
from ophyd_async.core import DEFAULT_TIMEOUT, Device
from ophyd_async.plan_stubs import ensure_connected

P = ParamSpec("P")


def _recursively_find_devices(obj) -> set[Device]:
    if isinstance(obj, Device):
        return {obj}
    if isinstance(obj, Sequence | Collection):
        return {dev for arg in obj for dev in _recursively_find_devices(arg)}
    if isinstance(obj, Mapping):
        return {
            dev
            for key, value in obj.items()
            for dev in _recursively_find_devices(key) | _recursively_find_devices(value)
        }
    return set()


def ensure_devices_connected(
    plan: Callable[P, MsgGenerator],
    mock: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    force_reconnect: bool = False,
) -> Callable[P, MsgGenerator]:
    def plan_with_connected_devices(*args: P.args, **kwargs: P.kwargs):
        devices = _recursively_find_devices(args) | _recursively_find_devices(kwargs)
        yield from ensure_connected(
            *devices, mock=mock, timeout=timeout, force_reconnect=force_reconnect
        )
        yield from plan(*args, **kwargs)

    return plan_with_connected_devices


ensure_devices_connected_decorator = make_decorator(ensure_devices_connected)
