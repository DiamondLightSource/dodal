from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class ElectromagnetMagnetField(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.field = epics_signal_rw(
                float, write_pv=prefix + "FIELD", read_pv=prefix + "FIELD:RBV"
            )
            self.current = epics_signal_rw(float, prefix + "DMD")
        super().__init__(name=name)
