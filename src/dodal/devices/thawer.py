from bluesky.protocols import Movable, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    OnOff,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw


class Thawer(StandardReadable, Stoppable, Movable[OnOff]):
    def __init__(self, prefix: str, name: str = "") -> None:
        self._control = epics_signal_rw(OnOff, prefix + ":CTRL")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: OnOff):
        await self._control.set(value)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        await self._control.set(OnOff.OFF)
