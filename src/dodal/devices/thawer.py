from bluesky.protocols import Stoppable
from ophyd_async.core import (
    AsyncStatus,
    OnOff,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw


class Thawer(StandardReadable, Stoppable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(OnOff, prefix + ":CTRL")
        super().__init__(name)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        await self.control.set(OnOff.OFF)
