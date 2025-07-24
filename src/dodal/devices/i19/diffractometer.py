from ophyd_async.epics.motor import Motor

from dodal.devices.motors import SixAxisGonio, Stage

# prefix: BL19I-MO-CIRC-02:SAM:


class DetectorMotion(Stage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.det_z = Motor(f"{prefix}DET")
            self.two_theta = Motor(f"{prefix}2THETA")
        super().__init__(name=name)


class FourCircleDiffractometer(SixAxisGonio):
    def __init__(self, prefix: str, name: str = ""):
        self.det_stage = DetectorMotion(prefix, name)
        super().__init__(prefix, name)
