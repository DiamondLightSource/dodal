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


def _current_count_per_sec(current_count: float, current_count_time: float) -> float:
    return current_count / current_count_time


def _voltage_per_sec(
    current_count_per_sec: float, current_count_per_volt: float
) -> float:
    return current_count_per_sec / current_count_per_volt


@default_mock_class(
    reset_signal_on_update_mock_factory(
        "trigger_start", CountState.COUNT, CountState.DONE
    )
)
class StruckScaler(CurrentAmpCounter):
    """StruckScaler is a counting card that records the output signal from a wide
    range of detectors. This class contains the basic control to run the struck scaler
    card together with a current amplifier. It has functions that provide conversion
    between count and voltage.

    Attributes:
        readout(SignalR): Scaler card output.
        count_mode (SignalR[CountMode]): Counting card setting.
        count_time (SignalRW([float]): Count time.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        current_count_per_volt=100000,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.current_count = epics_signal_r(float, prefix + suffix)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.count_mode = epics_signal_rw(CountMode, prefix + ":AutoCount")
            self.current_count_time = epics_signal_rw(float, prefix + ".TP")

        self.trigger_start = epics_signal_rw(CountState, prefix + ".CNT")
        self.current_count_per_volt, _ = soft_signal_r_and_setter(
            float, initial_value=current_count_per_volt
        )
        self.current_count_per_sec = derived_signal_r(
            _current_count_per_sec,
            current_count=self.current_count,
            current_count_time=self.current_count_time,
        )
        self.voltage_per_sec = derived_signal_r(
            _voltage_per_sec,
            current_count_per_sec=self.current_count_per_sec,
            current_count_per_volt=self.current_count_per_volt,
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.count_mode.set(CountMode.ONE_SHOT)

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.current_count_time.set(value)

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
        await self.count_mode.set(CountMode.AUTO)
