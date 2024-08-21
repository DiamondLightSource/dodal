from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)

from dodal.log import LOGGER


class LookupTable(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            # self.actual_transmission = epics_signal_r(float, prefix + "MATCH")
            print("test")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """
        value: transmission
        """
        LOGGER.debug("Updating the lookup table ")
        pass
