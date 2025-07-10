from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.core import (
    epics_signal_x,
)


class I11Robot(StandardReadable, Locatable):
    def __init__(self, prefix: str, name=""):
        self.start = epics_signal_x(prefix + "START.VAL")
        self.hold = epics_signal_x(prefix + "HOLD.VAL")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        pass

    # @AsyncStatus.wrap
    async def locate(self) -> Location:
        # setpoint readback
        return Location(setpoint=1, readback=1)
