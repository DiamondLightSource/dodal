from ophyd_async.core import InOut, StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class FluorescenceDetector(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.pos = epics_signal_rw(InOut, f"{prefix}CTRL")
        super().__init__(name)
