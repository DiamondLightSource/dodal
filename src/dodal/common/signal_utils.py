from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from bluesky.protocols import Reading
from ophyd_async.core import SignalR, SoftSignalBackend
from ophyd_async.core._soft_signal_backend import SignalMetadata

T = TypeVar("T")


class HarwareBackedSoftSignalBackend(SoftSignalBackend[T]):
    def __init__(
        self,
        get_from_hardware_func: Callable[[], Coroutine[Any, Any, T]],
        *args,
        **kwargs,
    ) -> None:
        self.get_from_hardware_func = get_from_hardware_func
        super().__init__(*args, **kwargs)

    async def _update_value(self):
        new_value = await self.get_from_hardware_func()
        await self.put(new_value)

    async def get_reading(self) -> Reading:
        await self._update_value()
        return await super().get_reading()

    async def get_value(self) -> T:
        await self._update_value()
        return await super().get_value()


def create_hardware_backed_soft_signal(
    datatype: type[T],
    get_from_hardware_func: Callable[[], Coroutine[Any, Any, T]],
    units: str | None = None,
    precision: int | None = None,
):
    """Creates a soft signal that, when read will call the function passed into
    `get_from_hardware_func` and return this.

    This will allow you to make soft signals derived from arbitrary hardware signals.
    However, calling subscribe on this signal does not give you a sensible value and
    the signal is currently read only. See https://github.com/bluesky/ophyd-async/issues/525
    for a more full solution.
    """
    metadata = SignalMetadata(units=units, precision=precision)
    return SignalR(
        backend=HarwareBackedSoftSignalBackend(
            get_from_hardware_func, datatype, metadata=metadata
        )
    )
