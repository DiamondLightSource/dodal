from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Stage, XYZStage

CIRC = "-MO-CIRC-02:"  # for phi, kappa, omega, 2theta and det_z
SAMP = "-MO-SAMP-02:"  # for x,y,z


class DetectorMotion(Stage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.det_z = Motor(f"{prefix}DET")
            self.two_theta = Motor(f"{prefix}2THETA")
        super().__init__(name=name)


# Collision model needs to be included
# See https://github.com/DiamondLightSource/dodal/issues/1073
class FourCircleDiffractometer(XYZStage):
    """Newport 4-circle diffractometer device."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        circ_infix: str = CIRC,
        samp_infix: str = SAMP,
    ):
        with self.add_children_as_readables():
            self.phi = Motor(f"{prefix}{circ_infix}SAM:PHI")
            self.omega = Motor(f"{prefix}{circ_infix}SAM:OMEGA")
            self.kappa = Motor(f"{prefix}{circ_infix}SAM:KAPPA")
            self.det_stage = DetectorMotion(f"{prefix}{circ_infix}SAM:", name)
        super().__init__(f"{prefix}{samp_infix}SAM:", name)
