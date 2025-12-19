from typing import TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, StrictEnum, soft_signal_rw


class SelectedSource(StrictEnum):
    SOURCE1 = "source1"
    SOURCE2 = "source2"


T = TypeVar("T")


def get_obj_from_selected_source(selected_source: SelectedSource, s1: T, s2: T) -> T:
    """Util function that maps enum values for SelectedSource to two objects. It then
    returns one of the objects that corrosponds to the selected_source value."""
    match selected_source:
        case SelectedSource.SOURCE1:
            return s1
        case SelectedSource.SOURCE2:
            return s2


class SourceSelector(StandardReadable, Movable[SelectedSource]):
    """Device that holds a selected_source signal enum of SelectedSource. Useful for
    beamlines with multiple sources to coordinate which energy source or shutter to use."""

    def __init__(self, name: str = ""):
        with self.add_children_as_readables():
            self.selected_source = soft_signal_rw(
                SelectedSource, SelectedSource.SOURCE1
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SelectedSource):
        await self.selected_source.set(value)
