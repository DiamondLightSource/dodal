from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw


# Equivalent to GDA SuperconductingMagnetControllerClass
class RampMagnetAxisController(StandardReadable, Movable[float]):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.ramp_rate_readback = epics_signal_rw(
                float, prefix + "STS:RAMPRATE:TPM"
            )
        self.ramp_rate_demand = epics_signal_rw(float, prefix + "SET:DMD:RAMPRATE:TPM")
        self.limit = epics_signal_rw(float, prefix + "LIM:RAMPRATE:TPM")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.ramp_rate_demand.set(value)


class RampMagnetControllerGroup(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = RampMagnetAxisController(prefix + "-01:")
            self.y = RampMagnetAxisController(prefix + "-02:")
            self.z = RampMagnetAxisController(prefix + "-03:")

        super().__init__(name)
