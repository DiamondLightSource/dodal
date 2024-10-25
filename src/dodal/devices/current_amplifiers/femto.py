from enum import Enum

from bluesky.protocols import Movable, Reading
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.log import LOGGER


class Fmeto100(str, Enum):
    sen_1 = "10^4"
    sen_2 = "10^5"
    sen_3 = "10^6"
    sen_4 = "10^7"
    sen_5 = "10^8"
    sen_6 = "10^9"
    sen_7 = "10^10"
    sen_8 = "10^11"
    sen_9 = "10^12"
    sen_10 = "10^13"


TIMEOUT = 0.5


class Femto(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(HintedSignal):
            self.gain = epics_signal_rw(Fmeto100, prefix + "GAIN")
            self.current = soft_signal_r_and_setter(
                float, initial_value=None, units="Amp"
            )
        with self.add_children_as_readables(ConfigSignal):
            self.auto_mode = soft_signal_rw(bool, initial_value=True)
        self.analogue_readout = epics_signal_r(float, prefix + "I")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if self.auto_mode.get_value is True:
            LOGGER.info(f"{self.name}-Attempting auto-gain")
            await self.auto_gain()

        self._set(value=value, timeout=TIMEOUT)

    @AsyncStatus.wrap
    async def _set(self, value, timeout=TIMEOUT) -> None:
        self.gain.set(value=value, timeout=timeout)

    async def read(self) -> dict[str, Reading]:
        self.current = await self.analogue_readout.get_value() * float(
            await self.gain.get_value()
        )
        return await super().read()

    async def auto_gain(self) -> bool:
        return True
        # check if analogure readout is within range
        # if so done
        # else
        #    change gain until it is within range
        #    or
        #    when it hit the edge of the range
        #    or
        #    when it tried the entire range.
