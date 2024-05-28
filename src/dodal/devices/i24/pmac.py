from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core.signal import SignalRW
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw

HOME_STR = r"\#1hmz\#2hmz\#3hmz"
ZERO_STR = "!x0y0z0"


class PMACStringMove(Triggerable):
    def __init__(
        self,
        pmac_str_sig: SignalRW,
        string_to_send: str,
    ) -> None:
        self.signal = pmac_str_sig
        self.cmd_string = string_to_send

    @AsyncStatus.wrap
    async def trigger(self):
        await self.signal.set(self.cmd_string, wait=True)


class PMAC(StandardReadable):
    """Device to control the chip stage on I24."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.pmac_string = epics_signal_rw(str, prefix + "PMAC_STRING")
        self.home = PMACStringMove(
            self.pmac_string,
            HOME_STR,
        )
        self.to_xyz_zero = PMACStringMove(self.pmac_string, ZERO_STR)

        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        super().__init__(name)
