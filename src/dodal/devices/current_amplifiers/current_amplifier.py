from abc import ABC, abstractmethod
from enum import Enum

from bluesky.protocols import (
    Movable,
    Preparable,
)
from ophyd_async.core import AsyncStatus, StandardReadable


class CurrentAmp(ABC, StandardReadable, Movable):
    """
    Base class for current amplifier, it contains the minimal functionality
     a current amplifier needs:

    Attributes:
        gain_conversion_table (Enum): The conversion table between current
        and gain setting.
    """

    def __init__(self, gain_conversion_table: type[Enum], name: str = "") -> None:
        self.gain_conversion_table = gain_conversion_table
        super().__init__(name)

    @abstractmethod
    async def increase_gain(self, value: int = 1) -> None:
        """Increase gain, increment by 1 by default.

        Returns:
            bool: True if success.
        """

    @abstractmethod
    async def decrease_gain(self, value: int = 1) -> None:
        """Decrease gain, decrement by 1 by default.

        Returns:
            bool: True if success.
        """

    @abstractmethod
    async def get_gain(self) -> Enum:
        """Get the current gain setting

        Returns:
            Enum: The member name of the current gain setting in gain_conversion_table.
        """

    @abstractmethod
    async def get_upperlimit(self) -> float:
        """Get the upper limit of the current amplifier"""

    @abstractmethod
    async def get_lowerlimit(self) -> float:
        """Get the lower limit of the current amplifier"""


class CurrentAmpCounter(ABC, StandardReadable, Preparable):
    """
    Base class for current amplifier counter, it contain the minimal implementations
      required for a counter/detector to function with CurrentAmpDet:

    Attributes:
        count_per_volt (float): The conversion factor between counter output and voltage.
    """

    def __init__(self, count_per_volt: float, name: str = ""):
        self.count_per_volt = count_per_volt
        super().__init__(name)

    @abstractmethod
    async def get_count(self) -> float:
        """ "Get count

        Returns:
            float: Current count
        """

    @abstractmethod
    async def get_count_per_sec(self) -> float:
        """Get count per second

        Returns:
            float: Current count per second
        """

    @abstractmethod
    async def get_voltage_per_sec(self) -> float:
        """Get count per second in voltage

        Returns:
            float: Current count in volt per second
        """

    @abstractmethod
    @AsyncStatus.wrap
    async def prepare(self, value: float) -> None:
        """Prepare method for setting up the counter"""
