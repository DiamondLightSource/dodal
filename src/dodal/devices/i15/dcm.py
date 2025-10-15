from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorBase,
    StationaryCrystal,
)


class ThetaYCrystal(StationaryCrystal):
    def __init__(self, prefix):
        with self.add_children_as_readables():
            self.theta = Motor(prefix + "THETA")
            self.y = Motor(prefix + "Y")
        super().__init__(prefix)


class ThetaRollYZCrystal(ThetaYCrystal):
    def __init__(self, prefix):
        with self.add_children_as_readables():
            self.roll = Motor(prefix + "ROLL")
            self.z = Motor(prefix + "Z")
        super().__init__(prefix)


class DCM(DoubleCrystalMonochromatorBase[ThetaRollYZCrystal, ThetaYCrystal]):
    """
    A double crystal monocromator device, used to select the beam energy.

    Once the i15 DCM supports all of the PVs required by BaseDCM, this class can be
    changed to inherit from BaseDCM and BaseDCMforI15 can be removed.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.calibrated_energy_in_kev = Motor(prefix + "CAL")
            self.x1 = Motor(prefix + "X1")
            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )

        super().__init__(prefix, ThetaRollYZCrystal, ThetaYCrystal, name)
