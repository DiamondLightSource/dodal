from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class ElectromagnetStage(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.y = Motor(prefix + "Y")
            self.pitch = Motor(prefix + "PITCH")
        super().__init__(name=name)
