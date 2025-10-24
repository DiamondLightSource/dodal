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
    A double crystal monochromator device, used to select the beam energy.

    Once the i15 DCM supports all of the PVs required by DoubleCrystalMonochromator or
    DoubleCrystalMonochromatorWithDSpacing this class can be changed to inherit from it,
    see https://jira.diamond.ac.uk/browse/I15-1053 for more info.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.calibrated_energy_in_keV = Motor(prefix + "CAL")
            self.x1 = Motor(prefix + "X1")

        super().__init__(prefix, ThetaRollYZCrystal, ThetaYCrystal, name)
