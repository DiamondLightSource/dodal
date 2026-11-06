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
    """CurrentAmpDet composed of a CurrentAmp and a CurrentAmpCounter. It provides
    the option for automatically changing the CurrentAmp gain to within the optimal
    range. It also converts the currentAmp/counter output back into the detector
    current output in Amp.

    Attributes:
        current_amp (currentAmp): Current amplifier type device.
        counter (CurrentAmpCounter): Counter that capture the current amplifier output.
        current (SignalRW([float]): Soft signal to store the corrected current.
        auto_mode (signalR([bool])): Soft signal to store the flag for auto gain.
        name (str): Name of the device.
    """

    def __init__(
        self,
        current_amp: CurrentAmp,
        counter: CurrentAmpCounter,
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
        super().__init__(name)

    async def read(self) -> dict[str, Reading]:
        """Read is modified so that if auto_mode is true it will optimise gain before
        taking the final reading.
        """
        if await self.auto_mode.get_value():
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()
            LOGGER.info(
                f"{self.name} new gain = {await self.current_amp().gain.get_value()}."
            )

        current = await self.get_corrected_current()
        self._set_current(current)
        return await super().read()

    @AsyncStatus.wrap
    async def auto_gain(self) -> None:
        upper_limit, lower_limit = await asyncio.gather(
            self.current_amp().upperlimit.get_value(),
            self.current_amp().lowerlimit.get_value(),
        )
        while True:
            # Acquire a fresh measurement at the new gain.
            await self.counter().trigger()

            voltage_per_sec = abs(await self.counter().get_voltage_per_sec())
            if voltage_per_sec > upper_limit:
                changed = await self.current_amp().decrease_gain()
            elif voltage_per_sec < lower_limit:
                changed = await self.current_amp().increase_gain()
            else:
                return

            if not changed:
                # Gain has just been moved to its limit. Acquire a measurement using
                # the final gain.
                await self.counter().trigger()
                return

    async def get_corrected_current(self) -> float:
        """Convert the output (count and gain) back into the read detector output in
        Amp.
        """
        current_gain, voltage_per_sec = await asyncio.gather(
            self.current_amp().gain.get_value(),
            self.counter().get_voltage_per_sec(),
        )
        corrected_current = voltage_per_sec / current_gain
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
