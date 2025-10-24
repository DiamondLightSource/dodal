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
    DoubleCrystalMonochromator,
    PitchAndRollCrystal,
    StationaryCrystal,
)


class DCM(DoubleCrystalMonochromator[PitchAndRollCrystal, StationaryCrystal]):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        prefix: str,
        xtal_prefix: str,
        name: str = "",
        crystal_metadata: CrystalMetadata | None = None,
    ) -> None:
        cm = crystal_metadata or make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        )
        with self.add_children_as_readables():
            self.perp_in_mm = Motor(prefix + "PERP")

            # temperatures
            self.xtal1_holder_temp = epics_signal_r(str, xtal_prefix + "PT100-1.SEVR")
            self.xtal1_temp = epics_signal_r(str, xtal_prefix + "PT100-2.SEVR")

            self.xtal2_heater_temp = epics_signal_r(str, xtal_prefix + "PT100-3.SEVR")
            self.xtal2_temp = epics_signal_r(str, xtal_prefix + "PT100-4.SEVR")

            self.xtal1_heater_temp = epics_signal_r(
                float, xtal_prefix + "H1:TTEMP:CALC"
            )
            self.xtal2_heater_temp = epics_signal_r(
                float, xtal_prefix + "H2:TTEMP:CALC"
            )

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
