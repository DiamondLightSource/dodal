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
    """Current amplifier detector composed of references to a current amplifier device
    and counter device.

    Provides automatic gain optimisation to keep the amplifier output within a configured
    voltage range and converts the counter output into the corresponding detector
    current in Amps.

    Automatic gain adjustment can be enabled or disabled via ``auto_mode`` signal.
    When enabled, the amplifier gain is optimised before the final counter
    acquisition.

    Attributes:
        current (SignalR[float]): Derived detector current in Amps, calculated from the
            counter output and amplifier sensitivity.
        auto_mode (SignalRW[bool]): Configuration signal controlling whether automatic
            gain optimisation is performed before acquisition.
    """

    def __init__(
        self,
        current_amp: CurrentAmp,
        counter: CurrentAmpCounter,
        auto_mode: bool = True,
        name: str = "",
    ) -> None:
        """Configure the current amplifier detector.

        Args:
            current_amp: Current amplifier providing the sensitivity and output voltage
                limits for gain optimisation.
            counter: Counter acquiring the current amplifier output.
            auto_mode: Whether to automatically optimise the amplifier gain before each
                acquisition.
            name: Name of the device.
        """
        self._current_amp_ref = Reference(current_amp)
        self._counter_ref = Reference(counter)
        with self.add_children_as_readables():
            self.current = derived_signal_r(
                _corrected_current,
                derived_units="A",
                voltage_per_sec=counter.voltage_per_sec,
                gain=current_amp.gain,
            )
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.auto_mode = soft_signal_rw(bool, initial_value=auto_mode)
        super().__init__(name)

    @AsyncStatus.wrap
    async def auto_gain(self) -> None:
        """Automatically optimise the current amplifier gain.

        Repeatedly trigger the counter and adjust the amplifier sensitivity
        until its output voltage is within the configured lower and upper
        limits. If the amplifier reaches its gain limit, return without
        further adjustment.
        """
        upper_limit, lower_limit = await asyncio.gather(
            self._current_amp_ref().upperlimit.get_value(),
            self._current_amp_ref().lowerlimit.get_value(),
        )
        while True:
            # Acquire a fresh measurement at the new gain.
            await self._counter_ref().trigger()

            voltage_per_sec = abs(await self._counter_ref().voltage_per_sec.get_value())
            if voltage_per_sec > upper_limit:
                self.log.debug(
                    f"Voltage is {voltage_per_sec} is above limit {upper_limit}. "
                    "Decreasing gain..."
                )
                changed = await self._current_amp_ref().decrease_gain()
            elif voltage_per_sec < lower_limit:
                self.log.debug(
                    f"Voltage {voltage_per_sec} is below limit {lower_limit}. "
                    "Increasing gain..."
                )
                changed = await self._current_amp_ref().increase_gain()
            else:
                self.log.debug("Don't need to adjust gain", self.name)
                break

            if not changed:
                direction = "decrease" if voltage_per_sec > upper_limit else "increase"
                self.log.warning(
                    f"Couldn't {direction} gain further. Input current might be out of range."
                )
                break

        LOGGER.debug("Finished optimising gain.")

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self._counter_ref().stage()

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self._counter_ref().prepare(value)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Trigger a detector acquisition.

        If automatic gain adjustment is enabled, optimise the amplifier gain
        before triggering the counter for the final acquisition. Otherwise,
        trigger the counter directly using the current amplifier gain.
        """
        if await self.auto_mode.get_value():
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()
            LOGGER.info(
                f"{self.name} new gain = {await self._current_amp_ref().gain.get_value()}."
            )
        await self._counter_ref().trigger()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self._counter_ref().unstage()
