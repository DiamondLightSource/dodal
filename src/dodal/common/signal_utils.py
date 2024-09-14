from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from bluesky.protocols import Reading
from event_model.documents.event_descriptor import DataKey
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

    async def get_datakey(self, source: str) -> DataKey:
        await self._update_value()
        return await super().get_datakey(source)

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
):
    metadata = SignalMetadata(units=units, precision=None)
    return SignalR(
        backend=HarwareBackedSoftSignalBackend(
            get_from_hardware_func, datatype, metadata=metadata
        )
    )
