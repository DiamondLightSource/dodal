from ophyd_async.core import Device
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, StationaryCrystal


class DCM(BaseDCM[PitchAndRollCrystal, StationaryCrystal]):
    """
    I09 double crystal monochromator (DCM), used to select the energy of the beam.
    The only difference atm is absence of WAVELENGTH record as compared to standard DCM
    and presence of LAMBDA record instead in epics.
    This DCM is available on i09 and i09_1 endstations.

    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Virtual motor PV's which set the physical motors so that the DCM produces requested
            # wavelength/energy
            self.energy_in_kev = Motor(prefix + "ENERGY")
            self.wavelength_in_a = Motor(prefix + "LAMBDA")

            # Real motors
            self.bragg_in_degrees = Motor(prefix + "BRAGG")
            # Offset ensures that the beam exits the DCM at the same point, regardless of energy.
            self.offset_in_mm = Motor(prefix + "OFFSET")

            self.crystal_metadata_d_spacing_a = epics_signal_r(
                float, prefix + "DSPACING:RBV"
            )

            super()._make_crystals(prefix, PitchAndRollCrystal, StationaryCrystal)

        Device.__init__(self, name)
