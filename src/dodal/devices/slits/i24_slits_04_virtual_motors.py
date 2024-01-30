from ophyd import Device, Component
from ophyd.status import StatusBase

from .slit_motor import SlitMotor
from .gap_and_centre_slit_base_classes import GapAndCentreSlit2d


class I24Slits04VirtualMotors(GapAndCentreSlit2d):
    x_centre: Device = Component(SlitMotor, "X:CENTER")
    x_size: Device = Component(SlitMotor, "X:SIZE")

    y_centre: Device = Component(SlitMotor, "Y:CENTER")
    y_size: Device = Component(SlitMotor, "Y:SIZE")

    def set(self, position_tuple):
        x_centre_value, x_size_value, y_centre_value, y_size_value = position_tuple

        status = StatusBase()
        status.set_finished()

        status &= self.x_centre.set(x_centre_value)
        status &= self.x_size.set(x_size_value)
        status &= self.y_centre.set(y_centre_value)
        status &= self.y_size.set(y_size_value)

        return status
