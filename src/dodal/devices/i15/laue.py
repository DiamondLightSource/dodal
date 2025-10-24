from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class LaueMonochrometer(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.bend = Motor(prefix + "BENDER")
            self.bragg = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
            self.yaw = Motor(prefix + "YAW")
            self.y = Motor(prefix + "Y")

        super().__init__(name)
