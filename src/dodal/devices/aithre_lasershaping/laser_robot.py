from enum import Enum

from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.devices.robot import BartRobot


class BeamlineSafe(Enum):
    ON = "On"
    NO = "No"
    OFF = "Off"


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        super().__init__(name=name, prefix=prefix)

        self.dewar_lid_heater = epics_signal_rw(str, prefix + "DW_1_CTRL")

        self.cryojet_retract = epics_signal_rw(str, prefix + "OP_24_FORCE_OPTION")
        self.set_beamline_safe = epics_signal_w(
            BeamlineSafe, prefix + "IP_16_FORCE_OPTION"
        )
        self.read_beamline_safe = epics_signal_r(bool, prefix + "ROBOT_IP_16_BITS.B0")
