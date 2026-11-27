import asyncio

from bluesky.protocols import Movable, Triggerable
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


def _current_in(voltage: float, gain: float) -> float:
    """Convert voltage output back into the current input in Amp."""
    return voltage / gain


class CurrentAmpDet(StandardReadable, Triggerable, Movable[float]):
    """Current amplifier detector composed of references to a current amplifier device
    and counter device.

    Provides automatic gain optimisation to keep the amplifier output within a configured
    voltage range and converts the counter output voltage into the corresponding detector
    current in. Units are in Amps.

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
                _current_in,
                derived_units="A",
                voltage=counter.voltage,
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
        further adjustment. On return, the counter holds a measurement taken
        at the final gain.
        """
        upper_limit, lower_limit = await asyncio.gather(
            self._current_amp_ref().upperlimit.get_value(),
            self._current_amp_ref().lowerlimit.get_value(),
        )
        max_attempts = len(self._current_amp_ref().sorted_gain_values)
        for _ in range(max_attempts):
            # Acquire a fresh measurement at the current gain.
            await self._counter_ref().trigger()

            voltage = abs(await self._counter_ref().voltage.get_value())

            if lower_limit <= voltage <= upper_limit:
                self.log.debug("Don't need to adjust gain")
                break

            if voltage > upper_limit:
                direction = "decrease"
                self.log.debug(
                    f"Voltage {voltage} is above limit {upper_limit}. "
                    "Decreasing gain..."
                )
                changed = await self._current_amp_ref().decrease_gain()
            else:
                direction = "increase"
                self.log.debug(
                    f"Voltage {voltage} is below limit {lower_limit}. "
                    "Increasing gain..."
                )
                changed = await self._current_amp_ref().increase_gain()

            if not changed:
                self.log.warning(
                    f"Couldn't {direction} gain further. "
                    "Input current might be out of range."
                )
                break
        else:
            self.log.warning(
                f"Reached maximum gain optimisation attempts of {max_attempts}."
            )
            # The gain was changed on the final attempt, so take a fresh
            # measurement at the final gain.
            await self._counter_ref().trigger()

        LOGGER.debug("Finished optimising gain.")

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await asyncio.gather(self._counter_ref().stage(), super().stage())

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """Set the counter integration time."""
        await self._counter_ref().set(value)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Trigger a detector acquisition.

        If automatic gain adjustment is enabled, optimise the amplifier gain;
        the final measurement taken during optimisation is used as the
        acquisition. Otherwise, trigger the counter directly using the current
        amplifier gain.
        """
        if await self.auto_mode.get_value():
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()
            LOGGER.info(
                f"{self.name} new gain = {await self._current_amp_ref().gain.get_value()}."
            )
        else:
            await self._counter_ref().trigger()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await asyncio.gather(self._counter_ref().unstage(), super().unstage())
