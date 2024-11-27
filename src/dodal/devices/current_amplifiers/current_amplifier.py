from abc import ABC, abstractmethod
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable


class CurrentAmp(ABC, StandardReadable, Movable):
    """
    Standard current amplifier, it contain the minimal functionality of a
     current amplifier:

     setting gain
     increment gain either increase or deceease gain.

    """

    def __init__(self, gain_convertion_table: type[Enum], name: str = "") -> None:
        self.gain_convertion_table = gain_convertion_table
        super().__init__(name)

    @abstractmethod
    async def increase_gain(self) -> bool: ...
    @abstractmethod
    async def decrease_gain(self) -> bool: ...
    @abstractmethod
    async def get_gain(self) -> str: ...


class CurrentAmpCounter(ABC, StandardReadable):
    def __init__(self, count_per_volt: float, name: str = ""):
        self.count_per_volt = count_per_volt
        super().__init__(name)

    @abstractmethod
    async def get_count(self) -> float: ...
    @abstractmethod
    async def get_count_per_sec(self) -> float: ...
    @abstractmethod
    async def get_voltage_per_sec(self) -> float: ...
    @abstractmethod
    @AsyncStatus.wrap
    async def prepare(self, value) -> None: ...
