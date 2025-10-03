from ophyd_async.epics.core import epics_signal_r, epics_signal_w
from ophyd_async.epics.motor import Motor

from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, RollCrystal


class DCM(BaseDCM[RollCrystal, PitchAndRollCrystal]):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        temperature_prefix: str,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.perp = Motor(prefix + "XTAL2:YPRIME")
            self.crystal_1_roll = Motor(prefix + "XTAL1:ROLL")
            self.crystal_2_roll = Motor(prefix + "XTAL2:ROLL")
            self.crystal_2_pitch = Motor(prefix + "XTAL2:PITCH")
            self.crystal_2_fine_pitch_read = epics_signal_r(
                float, prefix + "FPMTR:PREAD"
            )
            self.crystal_2_fine_pitch_write = epics_signal_w(
                float, prefix + "FPMTR:POUT"
            )
            self.crystal_2_fine_roll_read = epics_signal_r(
                float, prefix + "FRMTR:PREAD"
            )
            self.crystal_2_fine_roll_write = epics_signal_w(
                float, prefix + "FRMTR:POUT"
            )

            # Temperatures
            self.crystal_1_temp1 = epics_signal_r(float, temperature_prefix + "TMP1")
            self.crystal_2_temp2 = epics_signal_r(float, temperature_prefix + "TMP2")
            self.crystal_1_temp3 = epics_signal_r(float, temperature_prefix + "TMP3")
            self.crystal_2_temp4 = epics_signal_r(float, temperature_prefix + "TMP4")
            self.crystal_1_temp5 = epics_signal_r(float, temperature_prefix + "TMP5")
            self.crystal_2_temp6 = epics_signal_r(float, temperature_prefix + "TMP6")

        super().__init__(prefix, RollCrystal, PitchAndRollCrystal, name)
