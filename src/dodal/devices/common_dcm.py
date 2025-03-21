from typing import Generic, TypeVar

from ophyd_async.core import (
    DeviceVector,
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


Xtals = TypeVar("Xtals", bound=tuple[type[StationaryCrystal], type[StationaryCrystal]])


class BaseDCM(StandardReadable, Generic[Xtals]):
    """
    Common device for the double crystal monochromator (DCM), used to select the energy of the beam.

    Features common across all DCM's should include virtual motors to set energy/wavelength and contain two crystals,
    each of which can be movable. Some DCM's contain crystals with roll motors, and some contain crystals with roll and pitch motors.
    This base device accounts for all combinations of this.

    This device should act as a parent for beamline-specific DCM's, in which any other missing signals can be added.

    Bluesky plans using DCM's should be typed to specify which types of crystals are required
    """

    def __init__(self, prefix: str, crystal_type: Xtals, name: str = "") -> None:
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

            _device_vector_dict = self._make_device_vector_dict(prefix, crystal_type)
            self.crystals: DeviceVector[StationaryCrystal] = DeviceVector(
                _device_vector_dict
            )
        super().__init__(name)

    # Prefix convention is different depending on whether there are one or two controllable crystals
    def _make_device_vector_dict(
        self, prefix, crystal_types: Xtals
    ) -> dict[int, StationaryCrystal]:
        _device_vector_dict = {0: crystal_types[0](prefix)}
        if StationaryCrystal not in crystal_types:
            _device_vector_dict = {0: crystal_types[0](f"{prefix}XTAL1:")}
            _device_vector_dict[1] = crystal_types[1](f"{prefix}XTAL2:")
        else:
            _device_vector_dict = {0: crystal_types[0](f"{prefix}")}
        return _device_vector_dict
