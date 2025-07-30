from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.common_mirror import BaseMirror


class PiezoMirror(BaseMirror):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.fine_pitch = epics_signal_rw(
                float,
                read_pv=prefix + "FPITCH:RBV:AI",
                write_pv=prefix + "FPITCH:DMD:AO",
            )
        super().__init__(prefix, name)
