from ophyd_async.core import StandardReadable
from ophyd_async.sim.demo import SimMotor


class SimStage(StandardReadable):
    """MotorBundle with the axes of the Diamond AdSimulator"""

    def __init__(self, prefix: str, name: str = "sim"):
        with self.add_children_as_readables():
            self.x = SimMotor(prefix + "M1")
            self.y = SimMotor(prefix + "M2")
            self.z = SimMotor(prefix + "M3")
            self.theta = SimMotor(prefix + "M4")
            self.load = SimMotor(prefix + "M5")
        super().__init__(name=name)
