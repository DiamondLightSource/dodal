from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.devices.robot import BartRobot


class BeamlineSafe(StrictEnum):
    ON = "On"
    NO = "No"
    OFF = "Off"


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        self.dewar_lid_heater = epics_signal_rw(str, prefix + "DW_1_CTRL")

        self.cryojet_retract = epics_signal_rw(str, prefix + "OP_24_FORCE_OPTION")
        self.set_beamline_safe = epics_signal_w(
            BeamlineSafe, prefix + "IP_16_FORCE_OPTION"
        )
        self.read_beamline_safe = epics_signal_r(int, prefix + "ROBOT_IP_16_BITS.B0")
        super().__init__(name=name, prefix=prefix)
