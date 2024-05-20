from ophyd import Component, Device
from ophyd.status import StatusBase

from dodal.devices.slits.gap_and_center_slit_base_classes import GapAndCenterSlit2d
from dodal.devices.slits.slit_motor import SlitMotor


class I24Slits04VirtualMotors(GapAndCenterSlit2d):
    x_center: Device = Component(SlitMotor, "X:CENTRE")
    x_size: Device = Component(SlitMotor, "X:SIZE")

    x_center: Device = Component(SlitMotor, "Y:CENTRE")
    y_size: Device = Component(SlitMotor, "Y:SIZE")

    def set(self, position_tuple):
        x_center_value, x_size_value, x_center_value, y_size_value = position_tuple

        status = StatusBase()
        status.set_finished()

        status &= self.x_center.set(x_center_value)
        status &= self.x_size.set(x_size_value)
        status &= self.x_center.set(x_center_value)
        status &= self.y_size.set(y_size_value)

        return status

    def read(self):
        return (
            self.x_center.read(),
            self.x_size.read(),
            self.x_center.read(),
            self.y_size.read(),
        )
