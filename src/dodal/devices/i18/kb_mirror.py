from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class KBMirror(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        self._prefix = prefix
        with self.add_children_as_readables():
            self.x = epics_signal_rw(float, prefix + "X")
            self.y = epics_signal_rw(float, prefix + "Y")
            self.bend1 = epics_signal_rw(float, prefix + "BEND1")
            self.bend2 = epics_signal_rw(float, prefix + "BEND2")
            self.curve = epics_signal_rw(float, prefix + "CURVE")
            self.ellip = epics_signal_rw(float, prefix + "ELLIP")
        super().__init__(name=name)
