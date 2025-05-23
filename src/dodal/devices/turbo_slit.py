from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.motor import Motor


class TurboSlit(StandardReadable, Movable[float]):
    """
    This collection of motors coordinates time resolved XAS experiments.
    It selects a beam out of the polychromatic fan.
    There is a 0.1 degrees beam that can move along a 90-ish degree arc.
    A turboslit device moves after the beam, so that the gap aligns with the beam.
    The turboslit gap can be made smaller to increase energy resolution.
    The xfine motor can move the slit in x direction at high frequencies for different scans.
    These slits can be scanned continously or in step mode.
    The relationship between the three motors is as follows:
        - arc - position of the middle of the gap in degrees (coarse/ macro) extension
        - gap - width in mm, provides energy resolution
        - xfine - main scanning axis in mm, selects the energy as part of the high frequency scan
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.gap = Motor(prefix=prefix + "GAP")
            self.arc = Motor(prefix=prefix + "ARC")
            self.xfine = Motor(prefix=prefix + "XFINE")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """This will move the default XFINE"""
        await self.xfine.set(value)
