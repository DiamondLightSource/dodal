from ophyd import Component, Device

from dodal.devices.slits.gap_and_center_slit_base_classes import GapAndCenterSlit2d
from dodal.devices.slits.slit_motor import SlitMotor


class S5Bl02jAlSlits(GapAndCenterSlit2d):
    """Class to interact with slit simulator set up as BL02J temporary equipment.

    Many thanks to Andrew Foster!
    """

    y_plus: Device = Component(SlitMotor, "Y:PLUS")
    y_minus: Device = Component(SlitMotor, "Y:MINUS")

    x_plus: Device = Component(SlitMotor, "X:PLUS")
    x_minus: Device = Component(SlitMotor, "X:MINUS")

    y_size: Device = Component(SlitMotor, "Y:SIZE")
    y_center: Device = Component(SlitMotor, "Y:CENTER")

    x_size: Device = Component(SlitMotor, "X:SIZE")
    x_center: Device = Component(SlitMotor, "X:CENTER")

    def set(self, position_tuple: tuple[float, float, float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 4-tuple containing:
                x_center_value: Central x-coordinate of gap
                x_size_value: Width of gap in x-dimension
                y_center_value: Central y-coordinate of gap
                y_size_value: Width of gap in y-dimension
        """
        x_center_value, x_size_value, y_center_value, y_size_value = position_tuple

        status = self.x_center.set(x_center_value)
        status &= self.x_size.set(x_size_value)
        status &= self.y_center.set(y_center_value)
        status &= self.y_size.set(y_size_value)

        return status

    def read(self):
        return (
            self.x_center.read(),
            self.x_size.read(),
            self.y_center.read(),
            self.y_size.read(),
        )
