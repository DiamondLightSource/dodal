from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _X, _Y, _Z, Stage, XYZStage


class XYZPitchYawStage(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix="PITCH",
        yaw_infix="YAW",
    ):
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + pitch_infix)
            self.yaw = Motor(prefix + yaw_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class UpstreamDownstreamPair(Stage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.upstream = Motor(prefix + "US")
            self.downstream = Motor(prefix + "DS")
        super().__init__(name=name)
