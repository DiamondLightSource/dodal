from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class MultiLayerMirror(StandardReadable):
    """Multilayer Mirror"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.ds_x = Motor(prefix + "X2")
            self.ds_y = Motor(prefix + "J3")
            self.ib_y = Motor(prefix + "J1")
            self.ob_y = Motor(prefix + "J2")
            self.pitch = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
            self.us_x = Motor(prefix + "X1")
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.yaw = Motor(prefix + "YAW")

        super().__init__(name)
