from collections.abc import Callable, Coroutine
from typing import Any

from bluesky.protocols import Reading
from ophyd_async.core import SignalDatatypeT, SignalR, SoftSignalBackend


class HardwareBackedSoftSignalBackend(SoftSignalBackend[SignalDatatypeT]):
    def __init__(
        self,
        get_from_hardware_func: Callable[[], Coroutine[Any, Any, SignalDatatypeT]],
        *args,
        **kwargs,
    ) -> None:
        self.get_from_hardware_func = get_from_hardware_func
        super().__init__(*args, **kwargs)

    async def _update_value(self):
        new_value = await self.get_from_hardware_func()
        await self.put(new_value, True)

    async def get_reading(self) -> Reading:
        await self._update_value()
        return await super().get_reading()

    async def get_value(self) -> SignalDatatypeT:
        await self._update_value()
        return await super().get_value()


def create_hardware_backed_soft_signal(
    datatype: type[SignalDatatypeT],
    get_from_hardware_func: Callable[[], Coroutine[Any, Any, SignalDatatypeT]],
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
    return SignalR(
        backend=HardwareBackedSoftSignalBackend(
            get_from_hardware_func, datatype, units=units, precision=precision
        )
    )
