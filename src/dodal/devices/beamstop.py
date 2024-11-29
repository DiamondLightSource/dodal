from ophyd_async.core import Device
from ophyd_async.epics.motor import Motor
from ophyd_async.core import AsyncStatus
import asyncio


class Beamstop(Device):
    """

    Standard ophyd_async xyz motor stage, by combining 3 Motors,
    with added infix for extra flexibliy to allow different axes other than x,y,z.

    Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ["X", "Y", "Z"].
    Notes
    -----
    Example usage::
        async with DeviceCollector():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:")
    Or::
        with DeviceCollector():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:", suffix = ["A", "B", "C"])

    """

    def __init__(self, prefix: str, name: str, collection_position: list[float]):
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        self.collection_position = collection_position

        super().__init__(name=name)
    
    @AsyncStatus.wrap
    async def trigger(self):
        await self.z.set(self.collection_position[2])
        await asyncio.gather(
            self.x.set(self.collection_position[0]),
            self.y.set(self.collection_position[1]),
        )
