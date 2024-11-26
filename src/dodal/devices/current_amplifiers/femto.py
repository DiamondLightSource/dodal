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
    """These are the sensitivity setting for Femto 3xx current amplifier"""

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
     amplifiers, As the main different between all the DDPCACondition Femto is their gain table
     and respond time table.
    This class will allow the change of gain via set or the two incremental,
     increase_gain and decrease gain function.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[StrictEnum],
        gain_to_current_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.gain = epics_signal_rw(gain_table, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.gain_table = gain_table
            self.timeout = timeout
            self.raise_timetable = raise_timetable
        super().__init__(name=name, gain_convertion_table=gain_to_current_table)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if value not in [item.value for item in self.gain_convertion_table]:
            raise ValueError(f"Gain value {value} is not within {self.name} range.")
        sen_setting = self.gain_convertion_table(value).name
        LOGGER.info(f"{self.name} gain change to {sen_setting}:{value}")

        await self.gain.set(
            value=self.gain_table[sen_setting].value,
            timeout=self.timeout,
        )
        # wait for current amplifier to settle
        await asyncio.sleep(self.raise_timetable[sen_setting].value)

    async def increase_gain(self) -> bool:
        current_gain = int((await self.get_gain()).split("_")[-1])
        current_gain += 1
        if current_gain > len(self.gain_table):
            return False
        await self.set(self.gain_convertion_table[f"sen_{current_gain}"])
        return True

    async def decrease_gain(self) -> bool:
        current_gain = int((await self.get_gain()).split("_")[-1])
        current_gain -= 1
        if current_gain < 1:
            return False
        await self.set(self.gain_convertion_table[f"sen_{current_gain}"])
        return True

    async def get_gain(self) -> str:
        return (await self.gain.get_value()).name
