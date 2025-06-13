from typing import Generic, TypeVar

from ophyd_async.core import (
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor


class StationaryCrystal(StandardReadable):
    def __init__(self, prefix):
        super().__init__(prefix)


class RollCrystal(StationaryCrystal):
    def __init__(self, prefix):
        with self.add_children_as_readables():
            self.roll_in_mrad = Motor(prefix + "ROLL")
        super().__init__(prefix)


class PitchAndRollCrystal(StationaryCrystal):
    def __init__(self, prefix):
        with self.add_children_as_readables():
            self.pitch_in_mrad = Motor(prefix + "PITCH")
            self.roll_in_mrad = Motor(prefix + "ROLL")
        super().__init__(prefix)


Xtal_1 = TypeVar("Xtal_1", bound=StationaryCrystal)
Xtal_2 = TypeVar("Xtal_2", bound=StationaryCrystal)


class BaseDCM(StandardReadable, Generic[Xtal_1, Xtal_2]):
    """
    Common device for the double crystal monochromator (DCM), used to select the energy of the beam.

    Features common across all DCM's should include virtual motors to set energy/wavelength and contain two crystals,
    each of which can be movable. Some DCM's contain crystals with roll motors, and some contain crystals with roll and pitch motors.
    This base device accounts for all combinations of this.

    This device should act as a parent for beamline-specific DCM's, in which any other missing signals can be added.

    Bluesky plans using DCM's should be typed to specify which types of crystals are required. For example, a plan
    which only requires one crystal which can roll should be typed 'def my_plan(dcm: BaseDCM[RollCrystal, StationaryCrystal])`
    """

    def __init__(
        self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            # Virtual motor PV's which set the physical motors so that the DCM produces requested
            # wavelength/energy
            self.energy_in_kev = Motor(prefix + "ENERGY")
            self.wavelength_in_a = Motor(prefix + "WAVELENGTH")

            # Real motors
            self.bragg_in_degrees = Motor(prefix + "BRAGG")
            # Offset ensures that the beam exits the DCM at the same point, regardless of energy.
            self.offset_in_mm = Motor(prefix + "OFFSET")

            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )

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
