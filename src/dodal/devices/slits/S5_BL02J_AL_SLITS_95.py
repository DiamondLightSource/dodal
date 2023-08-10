from ophyd import Device, Component
from ophyd.status import StatusBase
from bluesky.protocols import Movable

from .slit_motor import SlitMotor
from .gap_and_centre_slit_base_classes import GapAndCentreSlit2d


class S5_BL02J_AL_SLITS_95(GapAndCentreSlit2d):
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

    def set(self, x_centre_value, x_size_value, y_centre_value, y_size_value):
        """Method to set position of slit.

        Parameters:
            x_centre_value: Central x-coordinate of gap
            x_size_value: Width of gap in x-dimension
            y_centre_value: Central y-coordinate of gap
            y_size_value: Width of gap in y-dimension
        """
        status = StatusBase()
        status.set_finished()

        status &= self.x_centre.set(x_centre_value)
        status &= self.x_size.set(x_size_value)
        status &= self.y_centre.set(y_centre_value)
        status &= self.y_size.set(y_size_value)

        return status
