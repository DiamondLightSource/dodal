"""
take an amp and detector with count
a flag for auto gain
if it set to true
    does auto gain before reading the detector count
    auto read will change the current amp setting so that the detector count is within
    a given range.

"""

from bluesky.protocols import Preparable, Reading
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmp
from dodal.devices.current_amplifiers.struck_scaler import StruckScaler
from dodal.log import LOGGER


class AutoGainDectector(StandardReadable, Preparable):
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
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
            self.upper_limit = upper_limit
            self.lower_limit = lower_limit
        super().__init__(name)

    async def read(self) -> dict[str, Reading]:
        if await self.auto_mode.get_value() is True:
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            if await self.auto_gain():
                LOGGER.info(
                    f"{self.name} new gain = f{await self.current_amp.get_gain()}."
                )
            else:
                LOGGER.warning("{self.name} new gain is at maximum/minimum value.")
        current = await self.get_corrected_current()
        self._current_set(current)
        return await super().read()

    async def auto_gain(self) -> bool:
        cnt = 0
        while cnt < len(self.current_amp.gain_convertion_table):
            # await self.counter.trigger()
            """
            negative value is possible on some current amplifier it is the order of
              magnitude that is important
            """
            reading = abs(await self.counter.get_voltage_per_sec())
            print(reading, cnt)
            if reading > self.upper_limit:
                if not await self.current_amp.decrease_gain():
                    return False
            elif reading < self.lower_limit:
                if not await self.current_amp.increase_gain():
                    return False
            else:
                break
            cnt += 1
        return True

    async def get_corrected_current(self) -> float:
        current_gain = await self.current_amp.get_gain()
        correction_factor = self.current_amp.gain_convertion_table[current_gain].value
        corrected_current = (
            await self.counter.get_voltage_per_sec()
        ) / correction_factor
        return corrected_current

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.counter.stage()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.counter.unstage()

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.counter.prepare(value=value)
