from ophyd_async.core import derived_signal_r

from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, StationaryCrystal


class DCM(BaseDCM[PitchAndRollCrystal, StationaryCrystal]):
    """
    I09 double crystal monochromator (DCM), used to select the energy of the beam.
    Differences:

    1. Can provide energy in eV via dcm.energy_in_ev read signal

    This DCM is available on i09 and i09_1 endstations.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, PitchAndRollCrystal, StationaryCrystal, name)
        self.energy_in_ev = derived_signal_r(
            self._convert_keV_to_eV, energy_signal=self.energy_in_kev.user_readback
        )
        # Set name so that new child signals get correct name
        # need to do it until https://github.com/bluesky/ophyd-async/pull/899 merged
        self.set_name(self.name)

    def _convert_keV_to_eV(self, energy_signal: float) -> float:
        return energy_signal * 1000
