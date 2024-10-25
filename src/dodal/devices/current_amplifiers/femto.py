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


class Femto100(str, Enum):
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


TIMEOUT = 0.5


class Femto(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(HintedSignal):
            self.gain = epics_signal_rw(Femto100, prefix + "GAIN")
            self.current, self._current_set = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )
        with self.add_children_as_readables(ConfigSignal):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
        self.analogue_readout = epics_signal_r(float, prefix + "I")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        self.gain.set(value=value, timeout=TIMEOUT)

    async def read(self) -> dict[str, Reading]:
        if await self.auto_mode.get_value() is True:
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()
        gain_value = 10 ** float((await self.gain.get_value()).value.split("^")[1])
        self._current_set(await self.analogue_readout.get_value() / gain_value)
        return await super().read()

    async def auto_gain(self) -> bool:
        cnt = 0
        success = True
        while success and cnt < len(Femto100):
            reading = await self.analogue_readout.get_value(cached=False)
            if reading > 9.8:
                current_gain = int((await self.gain.get_value()).name.split("_")[1])
                current_gain -= 1
                if current_gain < 1:
                    return False
                self.set(value=Femto100[f"sen_{current_gain}"])
            elif reading < 0.8:
                current_gain = int((await self.gain.get_value()).name.split("_")[1])
                current_gain += 1
                if current_gain > len(Femto100):
                    return False
                self.set(value=Femto100[f"sen_{current_gain}"])
            else:
                return True
            await asyncio.sleep(0.5)
            cnt += 1
        return True
