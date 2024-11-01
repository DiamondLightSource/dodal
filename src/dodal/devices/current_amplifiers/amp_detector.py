"""
take an amp and detector with count
a flag for auto gain
if it set to true
    does auto gain before reading the detector count
    auto read will change the current amp setting so that the detector count is within
    a given range.

"""

from bluesky.protocols import Reading
from ophyd_async.core import (
    ConfigSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
from dodal.devices.current_amplifiers.struck_scaler import StruckScaler
from dodal.log import LOGGER


class AutoGainDectector(StandardReadable):
    def __init__(
        self,
        current_amp: CurrentAmp,
        counter: StruckScaler,
        upper_limit: float,
        lower_limit: float,
        name: str = "",
    ) -> None:
        self.current_amp = current_amp
        self.counter = counter
        with self.add_children_as_readables():
            self.current, self._current_set = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )
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
                    f"{self.name} new gain = f{await self.current_amp.gain.get_value()}."
                )
            else:
                LOGGER.warning("{self.name} new gain is at maximum/minimum value.")
        current = await self.get_corrected_current()
        self._current_set(current)
        return await super().read()

    async def auto_gain(self) -> bool:
        cnt = 0
        count_time = await self.counter.count_time.get_value()
        while cnt < len(self.current_amp.gain_table):
            await self.counter.trigger()
            reading = await self.counter.readout.get_value(cached=False)
            if reading > self.upper_limit / count_time:
                if not await self.current_amp.decrease_gain():
                    return False
            elif reading < self.lower_limit / count_time:
                if not await self.current_amp.increase_gain():
                    return False
            else:
                return True
            cnt += 1
        return True

    async def get_corrected_current(self) -> float:
        current_gain = (await self.current_amp.gain.get_value()).name
        correction_factor = self.current_amp.gain_to_current_table[current_gain].value
        await self.counter.trigger()
        corrected_current = (
            await self.counter.readout.get_value(cached=False)
        ) / correction_factor
        return corrected_current
