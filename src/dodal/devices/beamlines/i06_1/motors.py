from ophyd_async.epics.motor import Motor

from dodal.devices.beamlines.i06_1.led_light import LEDLight
from dodal.devices.motors import XYZStage


class DiffractionDichroism(XYZStage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            # Motors
            self.theta = Motor(prefix + "THETA")
            self.theta2 = Motor(prefix + "DET:2THETA")
            self.chi = Motor(prefix + "CHI")
            self.phi = Motor(prefix + "PHI")
            self.dy = Motor(prefix + "DET:Y")

            # Camera lights
            self.cl1 = LEDLight(prefix + "LED1:")
            self.cl2 = LEDLight(prefix + "LED2:")
            self.cl3 = LEDLight(prefix + "LED3:")
            self.cl4 = LEDLight(prefix + "LED4:")
            self.cl5 = LEDLight(prefix + "LED5:")

        super().__init__(
            prefix, name, x_infix="SMPL:X", y_infix="SMPL:Y", z_infix="SMPL:Z"
        )
