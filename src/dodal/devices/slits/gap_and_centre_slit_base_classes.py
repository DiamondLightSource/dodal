from abc import abstractmethod
from bluesky.protocols import Movable
from ophyd import Device


class GapAndCentreSlit1d(Device, Movable):
    """Class defining interface between Ophyd and 1-dimensional gap and centre slits."""
    @abstractmethod
    def set(self, x_centre_value, x_size_value):
        """Method to set position of slit.
        
        Parameters:
            x_centre_value: Central coordinate of gap
            x_size_value: Width of gap
        """
        ...


class GapAndCentreSlit2d(Device, Movable):
    """Class defining interface between Ophyd and 2-dimensional gap and centre slits."""
    @abstractmethod
    def set(self, x_centre_value, x_size_value, y_centre_value, y_size_value):
        """Method to set position of slit.
        
        Parameters:
            x_centre_value: Central x-coordinate of gap
            x_size_value: Width of gap in x-dimension
            y_centre_value: Central y-coordinate of gap
            y_size_value: Width of gap in y-dimension
        """
        ...
