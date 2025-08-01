from ophyd_async.epics.core import epics_signal_r

from dodal.devices.common_dcm import (
    BaseDCM,
    PitchAndRollCrystal,
    RollCrystal,
)


class DCM(BaseDCM[RollCrystal, PitchAndRollCrystal]):
    """
    A double crystal monocromator device, used to select the beam energy.
    """

    def __init__(self, prefix: str, motion_prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Temperatures
            self.xtal1_temp = epics_signal_r(float, prefix + "PT100-1")
            self.xtal1_heater_temp = epics_signal_r(float, prefix + "PT100-2")
            self.xtal2_temp = epics_signal_r(float, prefix + "PT100-4")
            self.xtal2_heater_temp = epics_signal_r(float, prefix + "PT100-5")

            self.roll_plate_temp = epics_signal_r(float, prefix + "PT100-3")
            self.pitch_plate_temp = epics_signal_r(float, prefix + "PT100-6")
            self.backplate_temp = epics_signal_r(float, prefix + "PT100-7")
            self.b1_plate_temp = epics_signal_r(float, prefix + "PT100-7")
            self.gap_temp = epics_signal_r(float, prefix + "TC-1")

        super().__init__(motion_prefix, RollCrystal, PitchAndRollCrystal, name)
