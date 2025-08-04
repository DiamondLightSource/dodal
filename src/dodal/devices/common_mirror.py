from typing import Generic, TypeVar

from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.motors import _X, _Y, _Z, XYZPitchYawRollStage


class XYZPiezoCollimatingMirror(XYZPitchYawRollStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix: str = "PITCH",
        yaw_infix: str = "YAW",
        roll_infix: str = "ROLL",
        fpitch_read_suffix: str = "FPITCH:RBV",
        fpitch_write_suffix: str = "FPITCH:DMD",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + fpitch_read_suffix,
                write_pv=prefix + fpitch_write_suffix,
            )
        super().__init__(
            prefix, name, x_infix, y_infix, z_infix, pitch_infix, yaw_infix, roll_infix
        )


TMirror = TypeVar("TMirror", bound=StrictEnum)


class XYZSwitchingMirror(XYZPitchYawRollStage, Generic[TMirror]):
    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix: str = "PITCH",
        yaw_infix: str = "YAW",
        roll_infix: str = "ROLL",
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_r(mirrors, read_pv=prefix + mirror_read_suffix)
        super().__init__(
            prefix, name, x_infix, y_infix, z_infix, pitch_infix, yaw_infix, roll_infix
        )


class XYZPiezoSwitchingMirror(XYZPiezoCollimatingMirror, Generic[TMirror]):
    def __init__(
        self,
        prefix: str,
        mirrors: type[TMirror],
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix: str = "PITCH",
        yaw_infix: str = "YAW",
        roll_infix: str = "ROLL",
        fpitch_read_suffix: str = "FPITCH:RBV",
        fpitch_write_suffix: str = "FPITCH:DMD",
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_r(mirrors, read_pv=prefix + mirror_read_suffix)
        super().__init__(
            prefix,
            name,
            x_infix,
            y_infix,
            z_infix,
            pitch_infix,
            yaw_infix,
            roll_infix,
            fpitch_read_suffix,
            fpitch_write_suffix,
        )
