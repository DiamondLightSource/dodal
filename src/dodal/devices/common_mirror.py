from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class XYZCollMirror(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.yaw = Motor(prefix + "YAW")
            self.pitch = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
        super().__init__(prefix, name)


class XYZPiezoCollMirror(XYZCollMirror):
    def __init__(
        self,
        prefix: str,
        fpitch_read_suffix: str = "FPITCH:RBV",
        fpitch_write_suffix: str = "FPITCH:DMD",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
        super().__init__(prefix, name)
