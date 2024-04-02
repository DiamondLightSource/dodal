from ophyd_async.core import Device
from ophyd_async.epics.motion import Motor


class SimStage(Device):
    """MotorBundle with the axes of the Diamond AdSimulator"""

    def __init__(self, prefix: str, name: str = "sim"):
        self.x = Motor(prefix + "M1")
        self.y = Motor(prefix + "M2")
        self.z = Motor(prefix + "M3")
        self.theta = Motor(prefix + "M4")
        self.load = Motor(prefix + "M5")
        super().__init__(name=name)
