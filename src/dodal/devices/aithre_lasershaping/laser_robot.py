from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.enums import EnabledState
from dodal.devices.robot import BartRobot


class ForceBit(StrictEnum):
    ON = "On"
    NO = "No"
    OFF = "Off"


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        self.dewar_lid_heater = epics_signal_rw(
            EnabledState, prefix + "DW_1_ENABLED", prefix + "DW_1_CTRL"
        )
        self.cryojet_retract = epics_signal_rw(ForceBit, prefix + "OP_24_FORCE_OPTION")
        self.set_beamline_safe = epics_signal_rw(
            ForceBit, prefix + "IP_16_FORCE_OPTION"
        )
        super().__init__(name=name, prefix=prefix)
