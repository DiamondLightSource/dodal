import asyncio
import time

from bluesky.protocols import Reading
from event_model import DataKey
from ophyd_async.core import (
    DeviceVector,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r


class FilterState(StrictEnum):
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
    NUM_LENSES_FIELD_NAME = "number_of_lenses"

    def __init__(
        self,
        prefix: str,
        name: str = "",
        lens_geometry: str | None = None,
        cylindrical: bool | None = None,
        lens_material: str | None = None,
    ) -> None:
        self.filters = DeviceVector(
            {
                i: epics_signal_r(FilterState, f"{prefix}FILTER-{i:03}:STATUS_RBV")
                for i in range(FSwitch.NUM_FILTERS)
            }
        )
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            if lens_geometry is not None:
                self.lens_geometry, _ = soft_signal_r_and_setter(
                    str, initial_value=lens_geometry
                )
            else:
                self.lens_geometry = None

            if cylindrical is not None:
                self.cylindrical, _ = soft_signal_r_and_setter(
                    bool, initial_value=cylindrical
                )
            else:
                self.cylindrical = None

            if lens_material is not None:
                self.lens_material, _ = soft_signal_r_and_setter(
                    str, initial_value=lens_material
                )
            else:
                self.lens_material = None

        super().__init__(name)

    async def describe(self) -> dict[str, DataKey]:
        default_describe = await super().describe()
        return {
            FSwitch.NUM_LENSES_FIELD_NAME: DataKey(
                dtype="integer", shape=[], source=self.name
            ),
            **default_describe,
        }

    async def read(self) -> dict[str, Reading]:
        result = await asyncio.gather(
            *(filter.get_value() for filter in self.filters.values())
        )
        num_in = sum(r.value == FilterState.IN_BEAM for r in result)
        default_reading = await super().read()
        return {
            FSwitch.NUM_LENSES_FIELD_NAME: Reading(value=num_in, timestamp=time.time()),
            **default_reading,
        }
