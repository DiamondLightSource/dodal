from abc import ABC, abstractmethod
from typing import Tuple

from bluesky.protocols import Movable
from ophyd import Device


class GapAndCentreSlit1d(Device, Movable, ABC):
    """Class defining interface between Ophyd and 1-dimensional gap and centre slits."""

    @abstractmethod
    def set(self, position_tuple: Tuple[float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 2-tuple containing:
                x_centre_value: Central coordinate of gap
                x_size_value: Width of gap
        """
        ...


class GapAndCentreSlit2d(Device, Movable, ABC):
    """Class defining interface between Ophyd and 2-dimensional gap and centre slits."""

    @abstractmethod
    def set(self, position_tuple: Tuple[float, float, float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 4-tuple containing:
                x_centre_value: Central x-coordinate of gap
                x_size_value: Width of gap in x-dimension
                y_centre_value: Central y-coordinate of gap
                y_size_value: Width of gap in y-dimension
        """
        ...
