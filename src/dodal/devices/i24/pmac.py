from enum import Enum

from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core.signal import SignalRW
from ophyd_async.core.signal_backend import SignalBackend
from ophyd_async.core.soft_signal_backend import SoftSignalBackend
from ophyd_async.core.utils import DEFAULT_TIMEOUT
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw

HOME_STR = r"\#1hmz\#2hmz\#3hmz"
ZERO_STR = "!x0y0z0"


class LaserSettings(str, Enum):
    """PMAC strings to switch laser on and off.
    Note. On the PMAC, M strings usually have to do with position compare
    set up.
    For example, for laser1:
        Use M712 = 0 if triggering on falling edge.
        Use M712 = 1 if on rising edge.
    """

    LASER_1_ON = " M712=1 M711=1"
    LASER_1_OFF = " M712=0 M711=1"
    LASER_2_ON = " M812=1 M811=1"
    LASER_2_OFF = " M812=0 M811=1"


class PMACStringMove(Triggerable):
    """Trigger a PMAC move by setting the pmac_string."""

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


class PMACStringLaser(SignalRW):
    """Set the pmac_string control the laser."""

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        backend: SignalBackend,
        timeout: float | None = DEFAULT_TIMEOUT,
        name: str = "",
    ) -> None:
        self.signal = pmac_str_sig
        super().__init__(backend, timeout, name)

    @AsyncStatus.wrap
    async def set(self, laser_setting: LaserSettings):
        await self.signal.set(laser_setting.value, wait=True)


class PMAC(StandardReadable):
    """Device to control the chip stage on I24."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.pmac_string = epics_signal_rw(str, prefix + "PMAC_STRING")
        self.home = PMACStringMove(
            self.pmac_string,
            HOME_STR,
        )
        self.to_xyz_zero = PMACStringMove(self.pmac_string, ZERO_STR)

        self.laser = PMACStringLaser(self.pmac_string, backend=SoftSignalBackend(str))

        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        super().__init__(name)
