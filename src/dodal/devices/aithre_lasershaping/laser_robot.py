from ophyd_async.core import EnabledDisabled, OnOff, StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.robot import BartRobot


class ForceBit(StrictEnum):
    ON = OnOff.ON
    NO = "No"
    OFF = OnOff.OFF


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        self.dewar_lid_heater = epics_signal_rw(
            EnabledDisabled, prefix + "DW_1_ENABLED", prefix + "DW_1_CTRL"
        )
        self.cryojet_retract = epics_signal_rw(ForceBit, prefix + "OP_24_FORCE_OPTION")
        self.set_beamline_safe = epics_signal_rw(
            ForceBit, prefix + "IP_16_FORCE_OPTION"
        )
        super().__init__(name=name, prefix=prefix)
