from collections.abc import Callable, Coroutine
from typing import Any

from bluesky.protocols import Reading
from ophyd_async.core import SignalDatatypeT, SignalR, SignalRW, SoftSignalBackend

SetHardwareType = Callable[[SignalDatatypeT], Coroutine[Any, Any, None]]


class HardwareBackedSoftSignalBackend(SoftSignalBackend[SignalDatatypeT]):
    def __init__(
        self,
        get_from_hardware_func: Callable[[], Coroutine[Any, Any, SignalDatatypeT]],
        set_to_hardware_func: SetHardwareType | None = None,
        *args,
        **kwargs,
    ) -> None:
        self.get_from_hardware_func = get_from_hardware_func
        self.set_to_hardware_func = set_to_hardware_func
        super().__init__(*args, **kwargs)

    async def _update_value(self):
        new_value = await self.get_from_hardware_func()
        self.set_value(new_value)

    async def get_reading(self) -> Reading:
        await self._update_value()
        return await super().get_reading()

    async def get_value(self) -> SignalDatatypeT:
        await self._update_value()
        return await super().get_value()

    async def put(self, value: SignalDatatypeT | None, wait: bool) -> None:
        if self.set_to_hardware_func:
            write_value = self.initial_value if value is None else value
            await self.set_to_hardware_func(write_value)
        else:
            return await super().put(value, wait)


def create_rw_hardware_backed_soft_signal(
    datatype: type[SignalDatatypeT],
    get_from_hardware_func: Callable[[], Coroutine[Any, Any, SignalDatatypeT]],
    set_to_hardware_func: SetHardwareType,
    units: str | None = None,
    precision: int | None = None,
):
    """Creates a soft signal that, when read will call the function passed into
    `get_from_hardware_func` and return this. When set it will call `set_to_hardware_func`
    and send something to the hardware.

    This will allow you to make soft signals derived from arbitrary hardware signals.
    However, calling subscribe on this signal does not give you a sensible value. See https://github.com/bluesky/ophyd-async/issues/525
    for a more full solution.
    """
    return SignalRW(
        backend=HardwareBackedSoftSignalBackend(
            get_from_hardware_func,
            set_to_hardware_func,
            datatype,
            units=units,
            precision=precision,
        )
    )


def create_r_hardware_backed_soft_signal(
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
            get_from_hardware_func,
            None,
            datatype,
            units=units,
            precision=precision,
        )
    )
