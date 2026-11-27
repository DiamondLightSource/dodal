from ophyd_async.core import (
    AsyncStatus,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.current_amplifiers.current_amplifier import CurrentAmpCounter
from dodal.devices.scaler_card import ScalerCardController


class CountMode(StrictEnum):
    AUTO = "AutoCount"
    ONE_SHOT = "OneShot"


def _count_per_sec(count: float, integration_time: float) -> float:
    return count / integration_time


def _voltage_per_sec(count_per_sec: float, count_per_volt: float) -> float:
    return count_per_sec / count_per_volt


class StruckScaler(ScalerCardController, CurrentAmpCounter):
    """StruckScaler is a counting card that records the output signal from a wide
    range of detectors. This class extends :class:`ScalerCardController`, which
    provides the integration time and count control, with a single count channel
    and additional signals that provide conversion between count and voltage so it
    can be used together with a current amplifier.

    Attributes:
        count (SignalR[float]): Scaler card output.
        mode (SignalRW[CountMode]): Counting card setting.
        integration_time (SignalRW[float]): Count time.
        start_count (SignalRW[bool]): Start a count, returns to False when done.
        count_per_sec (SignalR[float]): Derived signal from the count and
            integration_time.
        count_per_volt (SignalR[float]): Conversion factor between counter output and
            voltage.
        voltage (SignalR[float]): The calculated voltage output from the count and
            count_per_volt.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        count_per_volt=100000,
        name: str = "",
    ):
        super().__init__(
            prefix=prefix, start_count_suffix=".CNT", count_suffix=".TP", name=name
        )
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.count = epics_signal_r(float, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(CountMode, prefix + ":AutoCount")

        self.count_per_volt, _ = soft_signal_r_and_setter(
            float, initial_value=count_per_volt
        )
        self.count_per_sec = derived_signal_r(
            _count_per_sec,
            count=self.count,
            integration_time=self.integration_time,
        )
        self.voltage = derived_signal_r(
            _voltage_per_sec,
            count_per_sec=self.count_per_sec,
            count_per_volt=self.count_per_volt,
        )

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.mode.set(CountMode.ONE_SHOT)
        await super().stage()

    @AsyncStatus.wrap
    async def prepare(self, value: float) -> None:
        """Set the integration time."""
        await self.set(value)

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.mode.set(CountMode.AUTO)
        await super().unstage()
