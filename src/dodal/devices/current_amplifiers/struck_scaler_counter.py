from ophyd_async.core import (
    AsyncStatus,
    StandardReadableFormat,
    StrictEnum,
    default_mock_class,
    derived_signal_r,
    set_and_wait_for_other_value,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.current_amplifiers import CurrentAmpCounter
from dodal.devices.util.mock_behaviour import reset_signal_on_update_mock_factory


class CountMode(StrictEnum):
    AUTO = "AutoCount"
    ONE_SHOT = "OneShot"


class CountState(StrictEnum):
    DONE = "Done"
    COUNT = "Count"


def _count_per_sec(count: float, count_time: float) -> float:
    return count / count_time


def _voltage_per_sec(count_per_sec: float, count_per_volt: float) -> float:
    return count_per_sec / count_per_volt


@default_mock_class(
    reset_signal_on_update_mock_factory(
        "trigger_start", CountState.COUNT, CountState.DONE
    )
)
class StruckScaler(CurrentAmpCounter):
    """StruckScaler is a counting card that records the output signal from a wide
    range of detectors. This class contains the basic control to run the struck scaler
    card together with a current amplifier. It has additional signals that provide
    conversion between count and voltage.

    Attributes:
        count(SignalR): Scaler card output.
        count_mode (SignalR[CountMode]): Counting card setting.
        count_time (SignalRW([float]): Count time.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        count_per_volt=100000,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.count = epics_signal_r(float, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(CountMode, prefix + ":AutoCount")
            self.count_time = epics_signal_rw(float, prefix + ".TP")

        self.count_per_volt, _ = soft_signal_r_and_setter(
            float, initial_value=count_per_volt
        )
        self.count_per_sec = derived_signal_r(
            _count_per_sec,
            count=self.count,
            count_time=self.count_time,
        )
        self.voltage_per_sec = derived_signal_r(
            _voltage_per_sec,
            count_per_sec=self.count_per_sec,
            count_per_volt=self.count_per_volt,
        )
        self.trigger_start = epics_signal_rw(CountState, prefix + ".CNT")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.mode.set(CountMode.ONE_SHOT)
        await super().stage()

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.count_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.trigger_start,
            set_value=CountState.COUNT,
            match_signal=self.trigger_start,
            match_value=CountState.DONE,
        )

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.mode.set(CountMode.AUTO)
        await super().unstage()
