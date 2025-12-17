from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Device, StrictEnum, soft_signal_rw


class SelectedSource(StrictEnum):
    SOURCE1 = "source1"
    SOURCE2 = "source2"


T = TypeVar("T")


def get_obj_from_selected_source(selected_source: SelectedSource, s1: T, s2: T) -> T:
    match selected_source:
        case SelectedSource.SOURCE1:
            return s1
        case SelectedSource.SOURCE2:
            return s2


class SourceSelector(Device, Movable[SelectedSource]):
    def __init__(self, name: str = ""):
        self.selected_source = soft_signal_rw(SelectedSource, SelectedSource.SOURCE1)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SelectedSource):
        await self.selected_source.set(value)
