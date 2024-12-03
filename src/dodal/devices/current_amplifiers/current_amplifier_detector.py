import asyncio

from bluesky.protocols import Preparable, Reading
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.current_amplifiers.current_amplifier import (
    CurrentAmp,
    CurrentAmpCounter,
)
from dodal.log import LOGGER


class CurrentAmpDet(StandardReadable, Preparable):
    """
    CurrentAmpDet composed of a CurrentAmp and a CurrentAmpCounter. It provides
      the option for automatically changing the CurrentAmp gain to within the optimal
      range. It also converts the currentAmp/counter output back into the detector
      current output in Amp.
    Attributes:
        current_amp (currentAmp): Current amplifier type device.
        counter (CurrentAmpCounter): Counter that capture the current amplifier output.
        current (SignalRW([float]): Soft signal to store the corrected current.
        auto_mode (signalR([bool])): Soft signal to store the flag for auto gain.
        upper_limit (float): The upper limit of the current amplifier output in volt.
        lower_limit (float): The lower limit of the current amplifier output in volt.
        name (str): Name of the device.
    """

    def __init__(
        self,
        current_amp: CurrentAmp,
        counter: CurrentAmpCounter,
        upper_limit: float,
        lower_limit: float,
        name: str = "",
    ) -> None:
        self.current_amp = Reference(current_amp)
        self.counter = Reference(counter)
        with self.add_children_as_readables():
            self.current, self._set_current = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
            self.upper_limit = upper_limit
            self.lower_limit = lower_limit
        super().__init__(name)

    async def read(self) -> dict[str, Reading]:
        """
        Read is modified so that if auto_mode is true it will optimise gain before
         taking the final reading
        """
        if await self.auto_mode.get_value():
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            if await self.auto_gain():
                LOGGER.info(
                    f"{self.name} new gain = {await self.current_amp().get_gain()}."
                )
            else:
                LOGGER.warning(f"{self.name} new gain is at maximum/minimum value.")
        current = await self.get_corrected_current()
        self._set_current(current)
        return await super().read()

    async def auto_gain(self) -> bool:
        for _ in range(0, len(self.current_amp().gain_conversion_table)):
            """
            negative value is possible on some current amplifier, hence the abs.
            """
            reading = abs(await self.counter().get_voltage_per_sec())
            if reading > self.upper_limit:
                if not await self.current_amp().decrease_gain():
                    return False
            elif reading < self.lower_limit:
                if not await self.current_amp().increase_gain():
                    return False
            else:
                break
        return True

    async def get_corrected_current(self) -> float:
        """
        Convert the output(count and gain) back into the read detector output in Amp.
        """
        current_gain, voltage_per_sec = await asyncio.gather(
            self.current_amp().get_gain(),
            self.counter().get_voltage_per_sec(),
        )
        correction_factor = self.current_amp().gain_conversion_table[current_gain].value
        corrected_current = voltage_per_sec / correction_factor
        return corrected_current

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.counter().stage()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.counter().unstage()

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.counter().prepare(value=value)
