from bluesky.protocols import Triggerable
from ophyd_async.core import StandardReadable
from ophyd_async.core.signal import SignalRW
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw


class PMACStringHome(Triggerable):
    def __init__(
        self,
        pmac_str_sig: SignalRW,
        string_to_send: str,
    ) -> None:
        self.signal = pmac_str_sig
        self.cmd_string = string_to_send
        super().__init__()

    async def trigger(self):
        await self.signal.set(self.cmd_string)


class PMAC(StandardReadable):  # Should it also be a movable?
    """Device to control the chip stage on I24."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.pmac_string = epics_signal_rw(str, prefix + "PMAC_STRING")
        # self.home = PMACStringHome(
        #     self.pmac_string, r"\#1hmz\#2hmz\#3hmz", backend=SoftSignalBackend(str)
        # )

        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        super().__init__(name)
