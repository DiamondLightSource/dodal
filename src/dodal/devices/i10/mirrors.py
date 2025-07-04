from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class PiezoMirror(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.yaw = Motor(prefix + "YAW")
            self.pitch = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + "FPITCH:RBV:AI",
                write_pv=prefix + "FPITCH:DMD:AO",
            )
        super().__init__(prefix, name)
