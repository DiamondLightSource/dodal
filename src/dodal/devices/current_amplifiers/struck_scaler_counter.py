from ophyd_async.core import (
    AsyncStatus,
    StandardReadableFormat,
    StrictEnum,
    set_and_wait_for_other_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.current_amplifiers import (
    CurrentAmpCounter,
)


class CountMode(StrictEnum):
    AUTO = "AutoCount"
    ONE_SHOT = "OneShot"


class CountState(StrictEnum):
    DONE = "Done"
    COUNT = "Count"


COUNT_PER_VOLTAGE = 100000


class StruckScaler(CurrentAmpCounter):
    """
    StruckScaler is a counting card that record the output signal from a wide
      range of detectors. This class contains the basic control to run the struckscaler
      card together with a current amplifier. It has functions that provide conversion
      between count and voltage.
    Attributes:
        readout(SignalR): Scaler card output.
        count_mode (SignalR[CountMode]): Counting card setting.
        count_time (SignalRW([float]): Count time.
    """

    def __init__(
        self, prefix: str, suffix: str, count_per_volt=COUNT_PER_VOLTAGE, name: str = ""
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readout = epics_signal_r(float, prefix + suffix)
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.count_mode = epics_signal_rw(CountMode, prefix + ":AutoCount")
            self.count_time = epics_signal_rw(float, prefix + ".TP")
        self.trigger_start = epics_signal_rw(CountState, prefix + ".CNT")
        super().__init__(count_per_volt=count_per_volt, name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.count_mode.set(CountMode.ONE_SHOT)

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.count_mode.set(CountMode.AUTO)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.trigger_start,
            set_value=CountState.COUNT,
            match_signal=self.trigger_start,
            match_value=CountState.COUNT,
        )

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.count_time.set(value)

    async def get_count(self) -> float:
        await self.trigger()
        return await self.readout.get_value()

    async def get_count_per_sec(self) -> float:
        return await self.get_count() / await self.count_time.get_value()

    async def get_voltage_per_sec(self) -> float:
        return await self.get_count_per_sec() / self.count_per_volt
