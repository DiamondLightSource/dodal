from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.motors import XYZPitchYawRollStage


class XYZPiezoCollimatingMirror(XYZPitchYawRollStage):
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


class XYZSwitchingMirror(XYZPitchYawRollStage):
    def __init__(
        self,
        prefix: str,
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_r(str, read_pv=prefix + mirror_read_suffix)
        super().__init__(prefix, name)


class XYZPiezoSwitchingMirror(XYZPiezoCollimatingMirror):
    def __init__(
        self,
        prefix: str,
        mirror_read_suffix: str = "MIRCTRL:RBV:MIRROR",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.mirror = epics_signal_r(str, read_pv=prefix + mirror_read_suffix)
        super().__init__(prefix, name)
