from abc import ABC, abstractmethod

from bluesky.protocols import Movable, Preparable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    SignalR,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)


class CurrentAmp(ABC, StandardReadable, Movable[float]):
    """Base class for current amplifier, it contains the minimal functionality
    a current amplifier needs.
    """

    gain: SignalRW[float]
    """Sensitivity in V/A."""

    def __init__(
        self,
        upperlimit: float,
        lowerlimit: float,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.upperlimit = soft_signal_rw(float, initial_value=upperlimit)
            self.lowerlimit = soft_signal_rw(float, initial_value=lowerlimit)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.gain.set(value)

    @abstractmethod
    async def increase_gain(self, value: int = 1) -> bool:
        """Increase gain, increment by 1 by default.

        Returns:
            bool: True if success.
        """

    @abstractmethod
    async def decrease_gain(self, value: int = 1) -> bool:
        """Decrease gain, decrement by 1 by default.

        Returns:
            bool: True if success.
        """


class CurrentAmpCounter(ABC, StandardReadable, Preparable, Triggerable):
    """Base class for current amplifier counter, it contain the minimal implementations
        required for a counter/detector to function with CurrentAmpDet.

    Attributes:
        count_per_volt (float): The conversion factor between counter output and voltage.
    """

    current_count: SignalR[float]
    current_count_per_sec: SignalR[float]
    current_count_per_volt: SignalR[float]
    voltage_per_sec: SignalR[float]

    @abstractmethod
    @AsyncStatus.wrap
    async def prepare(self, value: float) -> None:
        """Prepare method for setting up the counter."""

    @abstractmethod
    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Trigger acquisition of detector."""
