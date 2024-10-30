import asyncio
from enum import Enum

from bluesky.protocols import Movable, Reading
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.log import LOGGER


class Femto3xxGainTable(str, Enum):
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


class FemtoDDPCA(StandardReadable, Movable):
    """
    Femto current amplifier device, this class shouldcover all DDPCA Femto current
     amplifiers, As the main different between all the DDPCA Femto is their gain table
     and respond time table.
    This class will allow the change of gain via set or the two incremental,
     increase_gain and decrease gain function.
    """

    def __init__(
        self,
        prefix: str,
        gain_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(HintedSignal):
            self.gain = epics_signal_rw(gain_table, prefix + "GAIN")

        with self.add_children_as_readables(ConfigSignal):
            self.gain_table = gain_table
            self.timeout = timeout
            self.raise_timetable = raise_timetable
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
        print(await self.gain.get_value())
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


class FemtoAdcDetector(StandardReadable):
    def __init__(
        self,
        prefix: str,
        current_amp: FemtoDDPCA,
        upper_limit: float = 8.8,
        lower_limit: float = 0.8,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(HintedSignal):
            self.current_amp = current_amp
            self.current, self._current_set = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )

        with self.add_children_as_readables(ConfigSignal):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
            self.upper_limit = upper_limit
            self.lower_limit = lower_limit
        self.analogue_readout = epics_signal_r(float, prefix + "I")
        super().__init__(name)

    async def read(self) -> dict[str, Reading]:
        if await self.auto_mode.get_value() is True:
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            if await self.auto_gain():
                LOGGER.info(
                    f"{self.name} new gain = f{self.current_amp.gain.get_value()}."
                )
            else:
                LOGGER.warning("{self.name} new gain is at maximum/minimum value.")
        gain_value = 10 ** float(
            (await self.current_amp.gain.get_value()).value.split("^")[1]
        )
        self._current_set(await self.analogue_readout.get_value() / gain_value)
        return await super().read()

    async def auto_gain(self) -> bool:
        cnt = 0
        while cnt < len(self.current_amp.gain_table):
            reading = await self.analogue_readout.get_value(cached=False)
            if reading > self.upper_limit:
                if not await self.current_amp.decrease_gain():
                    return False
            elif reading < self.lower_limit:
                if not await self.current_amp.increase_gain():
                    return False
            else:
                return True
            await asyncio.sleep(0.5)
            cnt += 1
        return True
