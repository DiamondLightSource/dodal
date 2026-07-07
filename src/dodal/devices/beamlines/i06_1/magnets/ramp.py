from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw


# Equivalent to GDA SuperconductingMagnetControllerClass
class RampMagnetController(StandardReadable, Movable[float]):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.out = epics_signal_rw(float, prefix + "STS:RAMPRATE:TPM")
        self.in_ = epics_signal_rw(float, prefix + "SET:DMD:RAMPRATE:TPM")
        self.limit = epics_signal_rw(float, prefix + "LIM:RAMPRATE:TPM")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.in_.set(value)


class RampMagnetControllerGroup(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = RampMagnetController(prefix + "-01:")
            self.y = RampMagnetController(prefix + "-02:")
            self.z = RampMagnetController(prefix + "-03:")

        super().__init__(name)
