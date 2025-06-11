from ophyd_async.core import derived_signal_r

from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, StationaryCrystal


class DCM(BaseDCM[PitchAndRollCrystal, StationaryCrystal]):
    """
    I09 double crystal monochromator (DCM), used to select the energy of the beam.
    Differences:

    1. Can provide energy in eV.

    This DCM is available on i09 and i09_1 endstations.

    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, PitchAndRollCrystal, StationaryCrystal, name)
        with self.add_children_as_readables():
            self.energy_in_ev = derived_signal_r(
                self._convert_keV_to_eV, energy_signal=self.energy_in_kev.user_readback
            )

    def _convert_keV_to_eV(self, energy_signal: float) -> float:
        return energy_signal * 1000
