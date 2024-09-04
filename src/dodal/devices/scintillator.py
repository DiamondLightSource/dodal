from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class Scintillator(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.y = Motor(prefix + "-MO-SCIN-01:Y")
            self.z = Motor(prefix + "-MO-SCIN-01:Z")
        super().__init__(name)
