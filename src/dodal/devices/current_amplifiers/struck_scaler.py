from enum import Enum

from bluesky.protocols import Preparable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    HintedSignal,
    StandardReadable,
    set_and_wait_for_other_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class CountMode(str, Enum):
    auto = "AutoCount"
    one_shot = "OneShot"


class CountState(str, Enum):
    done = "Done"
    count = "Count"  # type: ignore


class StruckScaler(StandardReadable, Triggerable, Preparable):
    def __init__(self, prefix: str, suffix: str, name: str = ""):
        with self.add_children_as_readables(HintedSignal):
            self.readout = epics_signal_r(float, prefix + suffix)

        self.count_mode = epics_signal_rw(CountMode, prefix + ":AutoCount")
        self.count_time = epics_signal_rw(float, prefix + ".TP")
        self.trigger_start = epics_signal_rw(CountState, prefix + ".CNT")

        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.count_mode.set(CountMode.one_shot)

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.count_mode.set(CountMode.auto)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.trigger_start,
            set_value=CountState.count,
            read_signal=self.trigger_start,
            read_value=CountState.done,
        )

    @AsyncStatus.wrap
    async def prepare(self, value) -> None:
        await self.count_time.set(value)

    async def get_count(self) -> float:
        await self.trigger()
        return await self.readout.get_value()
