from abc import ABC, abstractmethod

from bluesky.protocols import Movable
from ophyd_async.core import (
    StandardReadable,
)


class CurrentAmp(ABC, StandardReadable, Movable):
    """
    Standard current amplifier, it contain the minimal functionality of a
     current amplifier:

     setting gain
     increment gain either increase or deceease gain.

    """

    def __init__(self, gain_convertion_table, name: str = "") -> None:
        self.gain_convertion_table = gain_convertion_table
        super().__init__(name)

    @abstractmethod
    async def increase_gain(self) -> bool: ...
    @abstractmethod
    async def decrease_gain(self) -> bool: ...
    @abstractmethod
    async def get_gain(self) -> str: ...
