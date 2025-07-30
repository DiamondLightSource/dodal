from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class BaseMirror(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.yaw = Motor(prefix + "YAW")
            self.pitch = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
        super().__init__(prefix, name)
