from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Stage, XYZStage

# prefix: BL19I-MO-CIRC-02:SAM: for phi, kappa, omega, 2theta and det_z
# prefix: BL19I-MO-SAMP-02:SAM: for x,y,z
# beacause of course... facepalm

CIRC = "-MO-CIRC-02:SAM:"
SAMP = "-MO-SAMP-02:SAM:"


class DetectorMotion(Stage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.det_z = Motor(f"{prefix}DET")
            self.two_theta = Motor(f"{prefix}2THETA")
        super().__init__(name=name)


class FourCircleDiffractometer(XYZStage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.phi = Motor(f"{prefix}{CIRC}PHI")
            self.omega = Motor(f"{prefix}{CIRC}OMEGA")
            self.kappa = Motor(f"{prefix}{CIRC}KAPPA")
        self.det_stage = DetectorMotion(f"{prefix}{CIRC}", name)
        super().__init__(f"{prefix}{SAMP}", name)
