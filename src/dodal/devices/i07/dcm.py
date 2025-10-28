from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromator,
    PitchAndRollCrystal,
    StationaryCrystal,
)


class DCM(DoubleCrystalMonochromator[PitchAndRollCrystal, StationaryCrystal]):
    """
    Device for i07's DCM, including temperature monitors and vertical motor which were
    included in GDA.
    """

    def __init__(
        self,
        motor_prefix: str,
        xtal_prefix: str,
        name: str = "",
    ) -> None:
        super().__init__(motor_prefix, PitchAndRollCrystal, StationaryCrystal, name)
        with self.add_children_as_readables():
            self.vertical_in_mm = Motor(motor_prefix + "PERP")

            # temperatures
            self.xtal1_temp = epics_signal_r(float, xtal_prefix + "PT100-2")
            self.xtal2_temp = epics_signal_r(float, xtal_prefix + "PT100-3")
            self.xtal1_holder_temp = epics_signal_r(float, xtal_prefix + "PT100-1")
            self.xtal2_holder_temp = epics_signal_r(float, xtal_prefix + "PT100-4")
            self.gap_motor = epics_signal_r(float, xtal_prefix + "TC-1")
            self.white_beam_stop_temp = epics_signal_r(float, xtal_prefix + "WBS:TEMP")
