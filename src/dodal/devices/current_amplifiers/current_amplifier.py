from abc import ABC, abstractmethod

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    SignalR,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)


class CurrentAmp(ABC, StandardReadable, Movable[float]):
    """Abstract base class for current amplifier devices.

    Provides a common interface for current amplifiers, including gain
    adjustment and configurable output voltage thresholds for automatic
    gain optimisation.

    Attributes:
        gain (SignalRW[float]): Current-to-voltage sensitivity in V/A.
        upperlimit (SignalRW[float]): Upper output voltage threshold in V
            used by automatic gain adjustment.
        lowerlimit (SignalRW[float]): Lower output voltage threshold in V
            used by automatic gain adjustment.
    """

    gain: SignalRW[float]
    sorted_gain_values: list[float]

    def __init__(
        self,
        upperlimit: float,
        lowerlimit: float,
        default_increase_gain: int = 1,
        default_decrease_gain: int = 1,
        name: str = "",
    ) -> None:
        """Configuration for the current amplifier.

        Args:
            upperlimit (float): Upper output voltage threshold in V for automatic
                gain adjustment.
            lowerlimit (float): Lower output voltage threshold in V for automatic
                gain adjustment.
            default_increase_gain: When calling increase_gain method with no args, what
                default value to use.
            default_decrease_gain: When calling decrease_gain method with no args, what
                default value to use.
            name (str): Name of the device (optional).
        """
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.upperlimit = soft_signal_rw(float, initial_value=upperlimit, units="V")
            self.lowerlimit = soft_signal_rw(float, initial_value=lowerlimit, units="V")

        self._default_increase_gain = default_increase_gain
        self._default_decrease_gain = default_decrease_gain
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.gain.set(value)

    async def increase_gain(self, value: int | None = None) -> bool:
        """Increase gain, increment by an optional amount. If not provided, then use a
        cofigured default.

        Returns:
            bool: True if success.
        """
        if value is None:
            value = self._default_increase_gain
        current_gain = await self.gain.get_value()
        current_index = self.sorted_gain_values.index(current_gain)
        target_index = current_index + value

        if target_index >= len(self.sorted_gain_values):
            await self.set(self.sorted_gain_values[-1])
            return False

        await self.set(self.sorted_gain_values[target_index])
        return True

    async def decrease_gain(self, value: int | None = None) -> bool:
        """Decrease gain, increment by an optional amount. If not provided, then use a
        cofigured default.

        Returns:
            bool: True if success.
        """
        if value is None:
            value = self._default_decrease_gain
        current_gain = await self.gain.get_value()
        current_index = self.sorted_gain_values.index(current_gain)
        target_index = current_index - value

        if target_index < 0:
            await self.set(self.sorted_gain_values[0])
            return False

        await self.set(self.sorted_gain_values[target_index])
        return True


class CurrentAmpCounter(ABC, StandardReadable, Triggerable, Movable[float]):
    """Base class for current amplifier counter, it contain the minimal implementations
    required for a counter/detector to function with CurrentAmpDet.
    """

    voltage: SignalR[float]

    @abstractmethod
    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """Set the counter integration time."""

    @abstractmethod
    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Trigger acquisition of detector."""
