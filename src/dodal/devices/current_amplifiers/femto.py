import asyncio
from enum import Enum

from bluesky.protocols import Reading
from ophyd_async.core import (
    ConfigSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.epics.signal import epics_signal_r

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
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


class FemtoDDPCA(CurrentAmp):
    """
    Femto current amplifier device, this class should cover all DDPCA Femto current
     amplifiers, As the main different between all the DDPCA Femto is their gain table
     and respond time table.
    This class will allow the change of gain via set or the two incremental,
     increase_gain and decrease gain function.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        gain_table: type[Enum],
        raise_timetable: type[Enum],
        timeout: float = 1,
        name: str = "",
    ) -> None:
        super().__init__(
            prefix=prefix,
            suffix=suffix,
            gain_table=gain_table,
            raise_timetable=raise_timetable,
            timeout=timeout,
            name=name,
        )


class FemtoAdcDetector(StandardReadable):
    def __init__(
        self,
        prefix: str,
        current_amp: CurrentAmp,
        upper_limit: float = 8.8,
        lower_limit: float = 0.8,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.current_amp = current_amp
            self.current, self._current_set = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )
            self.analogue_readout = epics_signal_r(float, prefix + "I")

        with self.add_children_as_readables(ConfigSignal):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
            self.upper_limit = upper_limit
            self.lower_limit = lower_limit
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
