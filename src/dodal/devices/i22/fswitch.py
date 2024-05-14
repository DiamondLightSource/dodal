import asyncio
import time
from enum import Enum
from typing import Dict

from bluesky.protocols import Reading
from ophyd_async.core import StandardReadable
from ophyd_async.core.device import DeviceVector
from ophyd_async.epics.signal import epics_signal_r


class FilterState(str, Enum):
    """
    Note that the in/out here refers to the internal rocker
    position so a PV value of IN implies a filter OUT of beam
    """

    IN_BEAM = "OUT"
    OUT_BEAM = "IN"


class FSwitch(StandardReadable):
    """
    Device for i22's fswitch. A filter switch for manipulating
    compound refractive lenses. Also referred to as a transfocator.

    This currently only implements the minimum
    functionality for retrieving the number of lenses inserted.

    Eventually this should be combined with the transfocator device in the i04
    module but is currently incompatible as the Epics interfaces are different.
    See https://github.com/DiamondLightSource/dodal/issues/399

    """

    NUM_FILTERS = 128

    def __init__(self, prefix: str, name: str = "") -> None:
        self.filters = DeviceVector(
            {
                i: epics_signal_r(FilterState, f"{prefix}FILTER-{i:03}:STATUS_RBV")
                for i in range(FSwitch.NUM_FILTERS)
            }
        )
        super().__init__(name)

    async def read(self) -> Dict[str, Reading]:
        result = await asyncio.gather(
            *(filter.get_value() for filter in self.filters.values())
        )
        num_in = sum(r.value == FilterState.IN_BEAM for r in result)
        default_reading = await super().read()
        return {
            "number_of_lenses": Reading(value=num_in, timestamp=time.time()),
            **default_reading,
        }
