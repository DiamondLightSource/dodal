from ophyd import Component, Device

from dodal.devices.slits.gap_and_centre_slit_base_classes import GapAndCentreSlit2d
from dodal.devices.slits.slit_motor import SlitMotor


class S5Bl02jAlSlits(GapAndCentreSlit2d):
    """Class to interact with slit simulator set up as BL02J temporary equipment.

    Many thanks to Andrew Foster!
    """

    y_plus: Device = Component(SlitMotor, "Y:PLUS")
    y_minus: Device = Component(SlitMotor, "Y:MINUS")

    x_plus: Device = Component(SlitMotor, "X:PLUS")
    x_minus: Device = Component(SlitMotor, "X:MINUS")

    y_size: Device = Component(SlitMotor, "Y:SIZE")
    y_centre: Device = Component(SlitMotor, "Y:CENTRE")

    x_size: Device = Component(SlitMotor, "X:SIZE")
    x_centre: Device = Component(SlitMotor, "X:CENTRE")

    def set(self, position_tuple: tuple[float, float, float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 4-tuple containing:
                x_centre_value: Central x-coordinate of gap
                x_size_value: Width of gap in x-dimension
                y_centre_value: Central y-coordinate of gap
                y_size_value: Width of gap in y-dimension
        """
        x_centre_value, x_size_value, y_centre_value, y_size_value = position_tuple

        status = self.x_centre.set(x_centre_value)
        status &= self.x_size.set(x_size_value)
        status &= self.y_centre.set(y_centre_value)
        status &= self.y_size.set(y_size_value)

        return status


    def read(self):
        return (
            self.x_centre.read(),
            self.x_size.read(),
            self.y_centre.read(),
            self.y_size.read()
        )