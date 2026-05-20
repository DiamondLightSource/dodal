import numpy as np
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.crystal_metadata import (
    CrystalMetadata,
)
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)


class DCM(
    DoubleCrystalMonochromatorWithDSpacing[PitchAndRollCrystal, StationaryCrystal]
):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        crystal_metadata: CrystalMetadata | None = None,
    ) -> None:
        with self.add_children_as_readables():
            self.energy_in_eV= epics_signal_r(float,prefix + )
            self.wavelength_in_a= epics_signal_r(float,prefix +)
            
