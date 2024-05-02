from typing import Type, TypeVar

from ophyd_async.core import SignalR, SignalRW, SimSignalBackend

T = TypeVar("T")


def create_soft_signal_rw(
    datatype: Type[T], name: str, source_prefix: str
) -> SignalRW[T]:
    return SignalRW(SimSignalBackend(datatype, f"sim://{source_prefix}:{name}"))


def create_soft_signal_r(
    datatype: Type[T], name: str, source_prefix: str
) -> SignalR[T]:
    return SignalR(SimSignalBackend(datatype, f"sim://{source_prefix}:{name}"))
