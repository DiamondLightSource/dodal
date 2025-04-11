import numpy as np
from ophyd_async.core import Array1D, soft_signal_r_and_setter
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.crystal_metadata import (
    CrystalMetadata,
    MaterialsEnum,
    make_crystal_metadata_from_material,
)
from dodal.devices.common_dcm import (
    BaseDCM,
    PitchAndRollCrystal,
    StationaryCrystal,
)


class DCM(BaseDCM[PitchAndRollCrystal, StationaryCrystal]):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        crystal_metadata: CrystalMetadata | None = None,
    ) -> None:
        cm = crystal_metadata or make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        )
        with self.add_children_as_readables():
            self.perp_in_mm = Motor(prefix + "PERP")

            # temperatures
            self.xtal1_temp = epics_signal_r(float, prefix + "TEMP1")
            self.xtal2_temp = epics_signal_r(float, prefix + "TEMP2")
            self.xtal1_heater_temp = epics_signal_r(float, prefix + "TEMP3")
            self.xtal2_heater_temp = epics_signal_r(float, prefix + "TEMP4")
            self.backplate_temp = epics_signal_r(float, prefix + "TEMP5")
            self.perp_temp = epics_signal_r(float, prefix + "TEMP6")
            self.perp_sub_assembly_temp = epics_signal_r(float, prefix + "TEMP7")

            self.crystal_metadata_usage, _ = soft_signal_r_and_setter(
                str, initial_value=cm.usage
            )
            self.crystal_metadata_type, _ = soft_signal_r_and_setter(
                str, initial_value=cm.type
            )
            reflection_array = np.array(cm.reflection)
            self.crystal_metadata_reflection, _ = soft_signal_r_and_setter(
                Array1D[np.uint64],
                initial_value=reflection_array,
            )
        super().__init__(prefix, PitchAndRollCrystal, StationaryCrystal, name)
