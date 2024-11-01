import asyncio
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
)
from ophyd_async.epics.signal import epics_signal_rw

from dodal.log import LOGGER


class CurrentAmp(StandardReadable, Movable):
    """
    Standard current amplifier, it contain the minimal functionality of a
     current amplifier:

     setting gain
     increment gain either increase or deceease gain.

    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[Enum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(HintedSignal):
            self.gain = epics_signal_rw(gain_table, prefix + suffix)

        with self.add_children_as_readables(ConfigSignal):
            self.gain_table = gain_table
            self.timeout = timeout
            self.raise_timetable = raise_timetable
        self.gain_to_current_table = gain_to_current_table
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if value not in self.gain_table.__members__:
            raise ValueError(f"Gain value {value} is not within {self.name} range.")
        LOGGER.info(f"{self.name} gain change to {value}")
        await self.gain.set(value=self.gain_table[value], timeout=self.timeout)
        # wait for current amplifier to settle
        await asyncio.sleep(self.raise_timetable[value].value)

    async def increase_gain(self) -> bool:
        current_gain = int((await self.gain.get_value()).name.split("_")[-1])
        current_gain += 1
        if current_gain > len(self.gain_table):
            return False
        await self.set(f"sen_{current_gain}")
        return True

    async def decrease_gain(self) -> bool:
        current_gain = int((await self.gain.get_value()).name.split("_")[-1])
        current_gain -= 1
        if current_gain < 1:
            return False
        await self.set(f"sen_{current_gain}")
        return True
