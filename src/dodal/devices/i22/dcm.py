import time

import numpy as np
from bluesky.protocols import Reading
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import (
    Array1D,
    StandardReadableFormat,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.crystal_metadata import CrystalMetadata
from dodal.devices.common_dcm import (
    BaseDCM,
    PitchAndRollCrystal,
    RollCrystal,
)

# Conversion constant for energy and wavelength, taken from the X-Ray data booklet
# Converts between energy in KeV and wavelength in angstrom
_CONVERSION_CONSTANT = 12.3984


class DCM(BaseDCM[RollCrystal, PitchAndRollCrystal]):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        temperature_prefix: str,
        crystal_1_metadata: CrystalMetadata,
        crystal_2_metadata: CrystalMetadata,
        prefix: str = "",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.perp = Motor(prefix + "PERP")

            # Temperatures
            self.backplate_temp = epics_signal_r(float, temperature_prefix + "PT100-7")
            self.perp_temp = epics_signal_r(float, temperature_prefix + "TC-1")
            self.crystal_1_temp = epics_signal_r(float, temperature_prefix + "PT100-1")
            self.crystal_1_heater_temp = epics_signal_r(
                float, temperature_prefix + "PT100-2"
            )
            self.crystal_2_temp = epics_signal_r(float, temperature_prefix + "PT100-4")
            self.crystal_2_heater_temp = epics_signal_r(
                float, temperature_prefix + "PT100-5"
            )

        # Soft metadata
        # If supplied include crystal details in output of read_configuration
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.crystal_1_usage, _ = soft_signal_r_and_setter(
                str, initial_value=crystal_1_metadata.usage
            )
            self.crystal_1_type, _ = soft_signal_r_and_setter(
                str, initial_value=crystal_1_metadata.type
            )
            self.crystal_1_reflection, _ = soft_signal_r_and_setter(
                Array1D[np.int32],
                initial_value=np.array(crystal_1_metadata.reflection),
            )
            self.crystal_1_d_spacing, _ = soft_signal_r_and_setter(
                float,
                initial_value=crystal_1_metadata.d_spacing[0],
                units=crystal_1_metadata.d_spacing[1],
            )
            self.crystal_2_usage, _ = soft_signal_r_and_setter(
                str, initial_value=crystal_2_metadata.usage
            )
            self.crystal_2_type, _ = soft_signal_r_and_setter(
                str, initial_value=crystal_2_metadata.type
            )
            self.crystal_2_reflection, _ = soft_signal_r_and_setter(
                Array1D[np.int32],
                initial_value=np.array(crystal_2_metadata.reflection),
            )
            self.crystal_2_d_spacing, _ = soft_signal_r_and_setter(
                float,
                initial_value=crystal_2_metadata.d_spacing[0],
                units=crystal_2_metadata.d_spacing[1],
            )

        super().__init__(prefix, RollCrystal, PitchAndRollCrystal, name)

    async def describe(self) -> dict[str, DataKey]:
        default_describe = await super().describe()
        return {
            f"{self.name}-wavelength_in_a": DataKey(
                dtype="number",
                shape=[],
                source=self.name,
                units="angstrom",
            ),
            **default_describe,
        }

    async def read(self) -> dict[str, Reading]:
        default_reading = await super().read()
        energy: float = default_reading[f"{self.name}-energy_in_kev"]["value"]
        if energy > 0.0:
            wavelength = _CONVERSION_CONSTANT / energy
        else:
            wavelength = 0.0

        return {
            **default_reading,
            f"{self.name}-wavelength_in_a": Reading(
                value=wavelength,
                timestamp=time.time(),
            ),
        }
