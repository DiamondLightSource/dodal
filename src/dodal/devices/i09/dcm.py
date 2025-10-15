from ophyd_async.epics.core import epics_signal_r

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromator,
    PitchAndRollCrystal,
    StationaryCrystal,
)


class DCM(DoubleCrystalMonochromator[PitchAndRollCrystal, StationaryCrystal]):
    """
    I09 double crystal monochromator (DCM), used to select the energy of the beam.
    Differences:

    1. Can provide energy in eV via dcm.energy_in_ev read signal

    This DCM is available on i09 and i09_1 endstations.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, PitchAndRollCrystal, StationaryCrystal, name)
        with self.add_children_as_readables():
            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )
