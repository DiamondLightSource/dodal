import asyncio

from bluesky.protocols import Preparable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_rw,
)

from dodal.devices.current_amplifiers.current_amplifier import (
    CurrentAmp,
    CurrentAmpCounter,
)
from dodal.log import LOGGER


def _corrected_current(voltage_per_sec: float, gain: float) -> float:
    """Convert the output (count and gain) back into the read detector output in Amp."""
    return voltage_per_sec / gain


class CurrentAmpDet(StandardReadable, Preparable, Triggerable):
    """CurrentAmpDet composed of a CurrentAmp and a CurrentAmpCounter. It provides
    the option for automatically changing the CurrentAmp gain to within the optimal
    range. It also converts the CurrentAmp / counter output back into the detector
    current output in Amp.

    Attributes:
        current_amp_ref (Reference[CurrentAmp]): Reference to current amplifier device.
        counter_ref (Reference[CurrentAmpCounter]): Reference to counter device that
            captures the current amplifier output.
        current (SignalRW[float]): Derived signal that calculates the corrected current.
        auto_mode (SignalR[bool]): Soft signal to store the flag for auto gain.
    """

    def __init__(
        self,
        current_amp: CurrentAmp,
        counter: CurrentAmpCounter,
        auto_mode: bool = True,
        name: str = "",
    ) -> None:
        self.current_amp_ref = Reference(current_amp)
        self.counter_ref = Reference(counter)
        with self.add_children_as_readables():
            self.current = derived_signal_r(
                _corrected_current,
                derived_units="I",
                voltage_per_sec=counter.voltage_per_sec,
                gain=current_amp.gain,
            )
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.auto_mode = soft_signal_rw(bool, initial_value=auto_mode)
        super().__init__(name)

    @AsyncStatus.wrap
    async def auto_gain(self) -> None:
        upper_limit, lower_limit = await asyncio.gather(
            self.current_amp_ref().upperlimit.get_value(),
            self.current_amp_ref().lowerlimit.get_value(),
        )
        while True:
            # Acquire a fresh measurement at the new gain.
            await self.counter_ref().trigger()

            voltage_per_sec = abs(await self.counter_ref().voltage_per_sec.get_value())
            if voltage_per_sec > upper_limit:
                changed = await self.current_amp_ref().decrease_gain()
            elif voltage_per_sec < lower_limit:
                changed = await self.current_amp_ref().increase_gain()
            else:
                return

            if not changed:
                return

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.counter_ref().stage()

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.counter_ref().prepare(value)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        if await self.auto_mode.get_value():
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()
            LOGGER.info(
                f"{self.name} new gain = {await self.current_amp_ref().gain.get_value()}."
            )
        await self.counter_ref().trigger()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.counter_ref().unstage()
