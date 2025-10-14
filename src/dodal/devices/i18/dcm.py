from ophyd_async.epics.core import epics_signal_r

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromator,
    PitchAndRollCrystal,
    RollCrystal,
)


class DCM(DoubleCrystalMonochromator[RollCrystal, PitchAndRollCrystal]):
    """
    A double crystal monocromator device, used to select the beam energy.

    Once spacing is added Si111 d-spacing is 3.135 angsterm , and Si311 is 1.637
    calculations are in gda/config/lookupTables/Si111/eV_Deg_converter.xml
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )

        super().__init__(prefix, RollCrystal, PitchAndRollCrystal, name)
