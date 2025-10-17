from typing import Generic, TypeVar

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor

from dodal.devices.common_dcm import (
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


Xtal_1 = TypeVar("Xtal_1", bound=StationaryCrystal)
Xtal_2 = TypeVar("Xtal_2", bound=StationaryCrystal)


class BaseDCMforI15(StandardReadable, Generic[Xtal_1, Xtal_2]):
    """
    Device for double crystal monochromators (DCM), which only allow energy of the beam to be selected.

    Features common across all DCM's should include virtual motors to set energy/wavelength and contain two crystals,
    each of which can be movable. Some DCM's contain crystals with roll motors, and some contain crystals with roll and pitch motors.
    This device only accounts for combinations of energy plus two crystals.

    This device is designed to be a drop in replacement for BaseDCM for i15, which doesn't require WAVELENGTH, BRAGG and OFFSET to
    be available. Once the i15 DCM supports all of the PVs required by BaseDCM, the i15 DCM device can switch to inheriting from
    BaseDCM and this class can be removed.
    """

    def __init__(
        self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            # Virtual motor PV's which set the physical motors so that the DCM produces requested
            # wavelength/energy
            self.energy_in_kev = Motor(prefix + "ENERGY")
            self._make_crystals(prefix, xtal_1, xtal_2)

        super().__init__(name)

    # Prefix convention is different depending on whether there are one or two controllable crystals
    def _make_crystals(self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2]):
        if StationaryCrystal not in [xtal_1, xtal_2]:
            self.xtal_1 = xtal_1(f"{prefix}XTAL1:")
            self.xtal_2 = xtal_2(f"{prefix}XTAL2:")
        else:
            self.xtal_1 = xtal_1(prefix)
            self.xtal_2 = xtal_2(prefix)


class DCM(BaseDCMforI15[ThetaRollYZCrystal, ThetaYCrystal]):
    """
    A double crystal monocromator device, used to select the beam energy.

    Once the i15 DCM supports all of the PVs required by BaseDCM, this class can be
    changed to inherit from BaseDCM and BaseDCMforI15 can be removed.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.calibrated_energy_in_kev = Motor(prefix + "CAL")
            self.x1 = Motor(prefix + "X1")

        super().__init__(prefix, ThetaRollYZCrystal, ThetaYCrystal, name)
