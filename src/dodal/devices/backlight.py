from asyncio import sleep

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, InOut, OnOff, StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class Backlight(StandardReadable, Movable[InOut]):
    """Simple device to trigger the pneumatic in/out."""

    TIME_TO_MOVE_S = 1.0  # Tested using a stopwatch on the beamline 09/2024

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.power = epics_signal_rw(OnOff, prefix + "-EA-BLIT-01:TOGGLE")
            self.position = epics_signal_rw(InOut, prefix + "-EA-BL-01:CTRL")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: InOut):
        """This setter will turn the backlight on when we move it in to the beam and off
        when we move it out.

        Moving the backlight in/out is a pneumatic axis and we have no readback on its
        position so it appears to us to instantly move. In fact it does take some time
        to move completely in/out so we sleep here to simulate this.
        """
        old_position = await self.position.get_value()
        await self.position.set(value)
        if value == InOut.OUT:
            await self.power.set(OnOff.OFF)
        else:
            await self.power.set(OnOff.ON)
        if old_position != value:
            await sleep(self.TIME_TO_MOVE_S)
