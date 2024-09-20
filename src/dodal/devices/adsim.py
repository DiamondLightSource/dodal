from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SimStage(StandardReadable):
    """MotorBundle with the axes of the Diamond AdSimulator"""

    def __init__(self, prefix: str, name: str = "sim"):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "M1")
            self.y = Motor(prefix + "M2")
            self.z = Motor(prefix + "M3")
            self.theta = Motor(prefix + "M4")
            self.load = Motor(prefix + "M5")
        super().__init__(name=name)
