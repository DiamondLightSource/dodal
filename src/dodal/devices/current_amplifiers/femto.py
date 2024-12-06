import asyncio
from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.current_amplifiers import CurrentAmp
from dodal.log import LOGGER


class Femto3xxGainTable(StrictEnum):
    """These are the sensitivity setting for Femto 3xx current amplifier"""

    sen_1 = "10^4"
    sen_2 = "10^5"
    sen_3 = "10^6"
    sen_4 = "10^7"
    sen_5 = "10^8"
    sen_6 = "10^9"
    sen_7 = "10^10"
    sen_8 = "10^11"
    sen_9 = "10^12"
    sen_10 = "10^13"


class Femto3xxGainToCurrentTable(float, Enum):
    """These are the voltage to current setting for Femto 3xx current amplifier"""

    sen_1 = 1e4
    sen_2 = 1e5
    sen_3 = 1e6
    sen_4 = 1e7
    sen_5 = 1e8
    sen_6 = 1e9
    sen_7 = 1e10
    sen_8 = 1e11
    sen_9 = 1e12
    sen_10 = 1e13


class Femto3xxRaiseTime(float, Enum):
    """These are the gain dependent raise time(s) for Femto 3xx current amplifier"""

    sen_1 = 0.8e-3
    sen_2 = 0.8e-3
    sen_3 = 0.8e-3
    sen_4 = 0.8e-3
    sen_5 = 2.3e-3
    sen_6 = 2.3e-3
    sen_7 = 17e-3
    sen_8 = 17e-3
    sen_9 = 350e-3
    sen_10 = 350e-3


class FemtoDDPCA(CurrentAmp):
    """
    Femto current amplifier device, this class should cover all DDPCA Femto current
      amplifiers, As the main different between all the DDPCA Femto is their gain table
        and response time table.
    Attributes:
        gain (SignalRW): This is the epic signal that control current amplifier gain.
        gain_table (strictEnum): The table epic use to set gain.
        upperlimit (float): upperlimit of the current amplifier
        lowerlimit (float): lowerlimit of the current amplifier
        timeout (float): Maximum waiting time in second for setting gain.
        raise_timetable (Enum): Table contain the minimum amount of time to wait after
         changing gain.

    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[StrictEnum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        upperlimit: float = 8.8,
        lowerlimit: float = 0.68,
        timeout: float = 1,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.gain = epics_signal_rw(gain_table, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.gain_table = gain_table
            self.timeout = timeout
            self.raise_timetable = raise_timetable
        self.upperlimit = upperlimit
        self.lowerlimit = lowerlimit
        super().__init__(name=name, gain_conversion_table=gain_to_current_table)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if value not in [item.value for item in self.gain_conversion_table]:
            raise ValueError(
                f"Gain value {value} is not within {self.name} range."
                + "\n Available gain:"
                + f" {[f'{c.value:.0e}' for c in self.gain_conversion_table]}"
            )
        sen_setting = self.gain_conversion_table(value).name
        LOGGER.info(f"{self.name} gain change to {sen_setting}:{value}")

        await self.gain.set(
            value=self.gain_table[sen_setting].value,
            timeout=self.timeout,
        )
        # wait for current amplifier's bandpass filter to settle.
        await asyncio.sleep(self.raise_timetable[sen_setting].value)

    @AsyncStatus.wrap
    async def increase_gain(self, value=1) -> bool:
        current_gain = int((await self.get_gain()).name.split("_")[-1])
        current_gain += value
        if current_gain > len(self.gain_table):
            return False
        await self.set(self.gain_conversion_table[f"sen_{current_gain}"])
        return True

    @AsyncStatus.wrap
    async def decrease_gain(self, value=1) -> bool:
        current_gain = int((await self.get_gain()).name.split("_")[-1])
        current_gain -= value
        if current_gain < 1:
            return False
        await self.set(self.gain_conversion_table[f"sen_{current_gain}"])
        return True

    @AsyncStatus.wrap
    async def get_gain(self) -> Enum:
        return self.gain_conversion_table[(await self.gain.get_value()).name]

    @AsyncStatus.wrap
    async def get_upperlimit(self) -> float:
        return self.upperlimit

    @AsyncStatus.wrap
    async def get_lowerlimit(self) -> float:
        return self.lowerlimit
