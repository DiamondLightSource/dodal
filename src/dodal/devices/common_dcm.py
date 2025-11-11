from typing import Generic, TypeVar

from ophyd_async.core import (
    StandardReadable,
    derived_signal_r,
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


class DoubleCrystalMonochromatorBase(StandardReadable, Generic[Xtal_1, Xtal_2]):
    """
    Base device for the double crystal monochromator (DCM), used to select the energy of the beam.

    Features common across all DCM's should include virtual motors to set energy/wavelength and contain two crystals,
    each of which can be movable. Some DCM's contain crystals with roll motors, and some contain crystals with roll and pitch motors.
    This base device accounts for all combinations of this.

    This device should act as a parent for beamline-specific DCM's which do not match the standard EPICS interface, it provides
    only energy and the crystal configuration.  Most beamlines should use DoubleCrystalMonochromator instead

    Bluesky plans using DCM's should be typed to specify which types of crystals are required. For example, a plan
    which only requires one crystal which can roll should be typed
    'def my_plan(dcm: DoubleCrystalMonochromatorBase[RollCrystal, StationaryCrystal])`
    """

    def __init__(
        self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            # Virtual motor PV's which set the physical motors so that the DCM produces requested energy
            self.energy_in_keV = Motor(prefix + "ENERGY")
            self.energy_in_eV = derived_signal_r(
                self._convert_keV_to_eV, energy_signal=self.energy_in_keV.user_readback
            )

            self._make_crystals(prefix, xtal_1, xtal_2)

        super().__init__(name)

    def _convert_keV_to_eV(self, energy_signal: float) -> float:  # noqa: N802
        return energy_signal * 1000

    # Prefix convention is different depending on whether there are one or two controllable crystals
    def _make_crystals(self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2]):
        if StationaryCrystal not in [xtal_1, xtal_2]:
            self.xtal_1 = xtal_1(f"{prefix}XTAL1:")
            self.xtal_2 = xtal_2(f"{prefix}XTAL2:")
        else:
            self.xtal_1 = xtal_1(prefix)
            self.xtal_2 = xtal_2(prefix)


class DoubleCrystalMonochromator(
    DoubleCrystalMonochromatorBase, Generic[Xtal_1, Xtal_2]
):
    """
    Common device for the double crystal monochromator (DCM), used to select the energy of the beam.

    Features common across all DCM's should include virtual motors to set energy/wavelength and contain two crystals,
    each of which can be movable. Some DCM's contain crystals with roll motors, and some contain crystals with roll and pitch motors.
    This base device accounts for all combinations of this.

    This device should act as a parent for beamline-specific DCM's, in which any other missing signals can be added.

    Bluesky plans using DCM's should be typed to specify which types of crystals are required. For example, a plan which only
    requires one crystal which can roll should be typed 'def my_plan(dcm: DoubleCrystalMonochromator[RollCrystal, StationaryCrystal])`
    """

    def __init__(
        self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2], name: str = ""
    ) -> None:
        super().__init__(prefix, xtal_1, xtal_2, name)
        with self.add_children_as_readables():
            # Virtual motor PV's which set the physical motors so that the DCM produces requested
            # wavelength
            self.wavelength_in_a = Motor(prefix + "WAVELENGTH")

            # Real motors
            self.bragg_in_degrees = Motor(prefix + "BRAGG")
            # Offset ensures that the beam exits the DCM at the same point, regardless of energy.
            self.offset_in_mm = Motor(prefix + "OFFSET")


class DoubleCrystalMonochromatorWithDSpacing(
    DoubleCrystalMonochromator, Generic[Xtal_1, Xtal_2]
):
    """
    Adds crystal D-spacing metadata to the DoubleCrystalMonochromator class.  This should be used in preference to the
    DoubleCrystalMonochromator on beamlines which have a "DSPACING:RBV" pv on their DCM.
    """

    def __init__(
        self, prefix: str, xtal_1: type[Xtal_1], xtal_2: type[Xtal_2], name: str = ""
    ) -> None:
        super().__init__(prefix, xtal_1, xtal_2, name)
        with self.add_children_as_readables():
            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )
