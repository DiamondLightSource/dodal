from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmpCounter
from dodal.devices.scaler_card import Struck32ChannelScaler

COUNT_PER_VOLTAGE = 100000


def _count_per_sec(count: float, integration_time: float) -> float:
    return count / integration_time


def _voltage_per_sec(count_per_sec: float, count_per_volt: float) -> float:
    return count_per_sec / count_per_volt


class StruckScalerChannel(CurrentAmpCounter):
    """A single channel of a :class:`Struck32ChannelScaler` card, for use with a current
    amplifier via :class:`CurrentAmpDet`.

    Setting and triggering are delegated to the shared card controller, so every
    channel on a card uses the same integration time and count. Staging is not
    delegated, as the controller stages its registered channels; the card's mode is
    set when the :class:`ScalerCard` (or controller) is staged. Channels are
    normally grouped in a custom device and given to a :class:`ScalerCard` with the
    controller, which registers them with the controller. Card level configuration
    (integration time, mode) is not repeated on each channel, as several channels of
    the same card are often read together. It has additional signals that provide
    conversion between count and voltage.

    Attributes:
        count (SignalR[float]): Scaler channel output.
        count_per_sec (SignalR[float]): Derived signal from the count and the
            controller integration_time.
        count_per_volt (SignalR[float]): Conversion factor between counter output and
            voltage.
        voltage (SignalR[float]): The calculated voltage output from the count and
            count_per_volt.
    """

    def __init__(
        self,
        controller: Struck32ChannelScaler,
        suffix: str,
        count_per_volt: float = COUNT_PER_VOLTAGE,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.count = epics_signal_r(float, controller.prefix + suffix)

        self.count_per_volt, _ = soft_signal_r_and_setter(
            float, initial_value=count_per_volt
        )
        self.count_per_sec = derived_signal_r(
            _count_per_sec,
            count=self.count,
            integration_time=controller.integration_time,
        )
        self.voltage = derived_signal_r(
            _voltage_per_sec,
            count_per_sec=self.count_per_sec,
            count_per_volt=self.count_per_volt,
        )
        self._controller_ref = Reference(controller)
        super().__init__(name=name)

    @property
    def controller(self) -> Struck32ChannelScaler:
        return self._controller_ref()

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """Set the integration time on the card controller."""
        await self.controller.set(value)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Start a count on the card controller and wait for it to complete."""
        await self.controller.trigger()
