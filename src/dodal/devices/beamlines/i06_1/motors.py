from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class DiffractionDichroism(XYZStage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.theta = Motor(prefix + "THETA")
            self.theta2 = Motor(prefix + "DET:2THETA")
            self.chi = Motor(prefix + "CHI")
            self.phi = Motor(prefix + "PHI")
            self.dy = Motor(prefix + "DET:Y")

        super().__init__(
            prefix, name, x_infix="SMPL:X", y_infix="SMPL:Y", z_infix="SMPL:Z"
        )
