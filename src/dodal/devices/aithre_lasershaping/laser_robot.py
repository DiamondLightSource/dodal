from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.robot import BartRobot


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        super().__init__(name=name, prefix=prefix)

        self.dewar_lid_heater = epics_signal_rw(str, prefix + "DW_1_CTRL")

        self.cryojet_retract = epics_signal_rw(str, prefix + "OP_24_FORCE_OPTION")
        self.beamline_safe = epics_signal_rw(str, prefix + "IP_16_FORCE_OPTION")
