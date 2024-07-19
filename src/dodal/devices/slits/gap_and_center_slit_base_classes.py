from abc import ABC, abstractmethod
from typing import Tuple

from bluesky.protocols import Movable
from ophyd import Device


class GapAndCenterSlit1d(Device, Movable, ABC):
    """Class defining interface between Ophyd and 1-dimensional gap and center slits."""

    @abstractmethod
    def set(self, position_tuple: Tuple[float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 2-tuple containing:
                x_center_value: Central coordinate of gap
                x_size_value: Width of gap
        """
        ...

    def read(self) -> Tuple[float, float]:
        """Method to read position of slit.

        Returns:
            Tuple of 2 floats containing:
                Central x-coordinate of gap
                Width of gap in x-dimension
        """
        ...


class GapAndCenterSlit2d(Device, Movable, ABC):
    """Class defining interface between Ophyd and 2-dimensional gap and center slits."""

    @abstractmethod
    def set(self, position_tuple: Tuple[float, float, float, float]):
        """Method to set position of slit.

        Parameters:
            position_tuple: A 4-tuple containing:
                x_center_value: Central x-coordinate of gap
                x_size_value: Width of gap in x-dimension
                y_center_value: Central y-coordinate of gap
                y_size_value: Width of gap in y-dimension
        """
        ...

    def read(self) -> Tuple[float, float, float, float]:
        """Method to read position of slit.

        Returns:
            Tuple of 4 floats containing:
                Central x-coordinate of gap
                Width of gap in x-dimension
                Central y-coordinate of gap
                Width of gap in y-dimension
        """
        ...
