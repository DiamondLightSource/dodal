from typing import Generic, TypeVar

from ophyd_async.core import StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

from dodal.devices.motors import _X, _Y, _Z, XYZPitchYawRollStage

TMirror = TypeVar("TMirror", bound=StrictEnum)


class XYZSwitchingMirror(XYZPitchYawRollStage, Generic[TMirror]):
    """
    Set of mirrors on a hexapod with x,y,z and yaw, pitch, roll motors. Mirrors is an stritcEnum class type of readback values, to change mirror one need to select and trigger mirror change.
    """

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
        mirror_write_suffix: str = "MIRCTRL:DMD:MIRROR",
        mirror_change_suffix: str = "MIRCTRL:SEQ:CHNG:MIRROR.PROC",
        mirror_abort_suffix: str = "MIRCTRL:DMD:ABORT.PROC",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_rw(
                mirrors,
                read_pv=prefix + mirror_read_suffix,
                write_pv=prefix + mirror_write_suffix,
            )

        self.mirror_change = epics_signal_x(write_pv=prefix + mirror_change_suffix)
        self.mirror_abort = epics_signal_x(write_pv=prefix + mirror_abort_suffix)

        super().__init__(
            prefix, name, x_infix, y_infix, z_infix, pitch_infix, yaw_infix, roll_infix
        )


class XYZPiezoCollimatingMirror(XYZPitchYawRollStage):
    """
    Collimating mirror on a hexapod with x,y,z and yaw, pitch, roll motors.
    In addition there is a fine pitch piezo motor.
    """

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


class XYZPiezoSwitchingMirror(XYZPiezoCollimatingMirror, Generic[TMirror]):
    """
    Set of mirrors on a hexapod with x,y,z and yaw, pitch, roll motors. Mirrors is an stritcEnum class type of readback values, to change mirror one need to select and trigger mirror change. In addition there is a fine pitch piezo motor.
    """

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
        mirror_write_suffix: str = "MIRCTRL:DMD:MIRROR",
        mirror_change_suffix: str = "MIRCTRL:SEQ:CHNG:MIRROR.PROC",
        mirror_abort_suffix: str = "MIRCTRL:DMD:ABORT.PROC",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_rw(
                mirrors,
                read_pv=prefix + mirror_read_suffix,
                write_pv=prefix + mirror_write_suffix,
            )

        self.mirror_change = epics_signal_x(write_pv=prefix + mirror_change_suffix)
        self.mirror_abort = epics_signal_x(write_pv=prefix + mirror_abort_suffix)

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
