from bluesky.protocols import Locatable, Location
from ophyd_async.core import AsyncStatus, StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_rw


class FlipMirror(StandardReadable, Locatable[bool]):
    """A mirror mounted on a Thorlabs MFF two-position flip mount, controlled via FastCS.

    Attributes:
        position (SignalRW[bool]): Whether the mirror is flipped.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.position = epics_signal_rw(
                bool, read_pv=f"{prefix}Position_RBV", write_pv=f"{prefix}Position"
            )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: bool):
        await self.position.set(value)

    async def locate(self) -> Location[bool]:
        return await self.position.locate()
