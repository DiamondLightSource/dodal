from functools import cached_property

from ophyd_async.core import (
    MovableLogic,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    TimeoutCalculator,
)
from ophyd_async.epics.core import epics_signal_rw


class RampRateMovableLogic(MovableLogic[float]):
    async def move(self, new_position: float, timeout: TimeoutCalculator):
        await self.setpoint.set(new_position, timeout=timeout())


# Equivalent to GDA SuperconductingMagnetControllerClass
class MagnetAxisRampRateController(StandardMovable[float], StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_rw(float, prefix + "STS:RAMPRATE:TPM")
        self.demand = epics_signal_rw(float, prefix + "SET:DMD:RAMPRATE:TPM")
        self.limit = epics_signal_rw(float, prefix + "LIM:RAMPRATE:TPM")
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> RampRateMovableLogic:
        return RampRateMovableLogic(readback=self.readback, setpoint=self.demand)


class MagnetThreeAxesRampRateController(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = MagnetAxisRampRateController(prefix + "-01:")
            self.y = MagnetAxisRampRateController(prefix + "-02:")
            self.z = MagnetAxisRampRateController(prefix + "-03:")

        super().__init__(name)
