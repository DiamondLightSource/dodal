from ophyd_async.epics.core import (
    epics_signal_rw,
    epics_signal_rw_rbv,
)

from dodal.devices.robot import BartRobot


class LaserRobot(BartRobot):
    def __init__(self, name: str, prefix: str) -> None:
        super().__init__(name=name, prefix=prefix)
        self.dewar_lid_temperature = epics_signal_rw(
            float, prefix + "DW_1_SET_POINT", prefix + "DW_1_TEMP"
        )
        self.dewar_lid_heater = epics_signal_rw_rbv(str, prefix + "DW_1_CTRL")

        self.cryojet_retract = epics_signal_rw_rbv(float, prefix + "OP_24_FORCE_OPTION")
        self.beamline_safe = epics_signal_rw_rbv(
            float, prefix + "IP_16_FORCE_OPTION"
        )  # 0 for on, 1 for no, 2 for off
