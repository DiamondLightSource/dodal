from asyncio import sleep
from enum import Enum, IntEnum
from typing import SupportsFloat

from bluesky.protocols import Triggerable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    CalculateTimeout,
    SignalBackend,
    SignalR,
    SignalRW,
    SoftSignalBackend,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.motor import Motor
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

HOME_STR = r"\#1hmz\#2hmz\#3hmz"  # Command to home the PMAC motors
ZERO_STR = "!x0y0z0"  # Command to blend any ongoing move into new position


class ScanState(IntEnum):
    RUNNING = 1
    DONE = 0


class LaserSettings(str, Enum):
    """PMAC strings to switch laser on and off.
    Note. On the PMAC, M-variables usually have to do with position compare
    set up.
    For example, for laser1:
        Use M712 = 0 if triggering on falling edge.
        Use M712 = 1 if on rising edge.
    """

    LASER_1_ON = " M712=1 M711=1"
    LASER_1_OFF = " M712=0 M711=1"
    LASER_2_ON = " M812=1 M811=1"
    LASER_2_OFF = " M812=0 M811=1"


class EncReset(str, Enum):
    """PMAC strings for position compare on encoder channels in the controller.

    For example, for ENC5:
        m508 sets position A to be compared with value in Channel5 in the controller.
        m509 sets position B to be compared with value in Channel5 in the controller.
    Note. These settings are usually used for initialisation.
    """

    ENC5 = "m508=100 m509=150"
    ENC6 = "m608=100 m609=150"
    ENC7 = "m708=100 m709=150"
    ENC8 = "m808=100 m809=150"


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
    """Set the pmac_string to control the laser."""

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
    async def set(
        self,
        value: LaserSettings,
        wait=True,
        timeout=CalculateTimeout,
    ):
        await self.signal.set(value.value, wait, timeout)


class PMACStringEncReset(SignalRW):
    """Set a pmac_string to control the encoder channels in the controller."""

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
    async def set(
        self,
        value: EncReset,
        wait=True,
        timeout=CalculateTimeout,
    ):
        await self.signal.set(value.value, wait, timeout)


class ProgramRunner(SignalRW):
    """Trigger the collection by setting the program number on the PMAC string.

    Once the program number has been set, wait for the collection to be complete.
    This will only be true when the status becomes 0.
    """

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        status_sig: SignalR,
        backend: SignalBackend,
        timeout: float | None = DEFAULT_TIMEOUT,
        name: str = "",
    ) -> None:
        self.signal = pmac_str_sig
        self.status = status_sig
        super().__init__(backend, timeout, name)

    @AsyncStatus.wrap
    async def set(self, value: int, wait=True, timeout=None):
        """ Set the pmac string to the program number and then wait for the scan to \
        finish running.
        This is done by checking the scan status PV which will go to 1 once the motion \
        program starts and back to 0 when it's done. The timeout passed to this set \
        should then be the total time required by the scan to finish.
        """
        prog_str = f"&2b{value}r"
        assert isinstance(timeout, SupportsFloat) or (
            timeout is None
        ), f"ProgramRunner does not support calculating timeout itself, {timeout}"
        await self.signal.set(prog_str, wait=wait)
        # First wait for signal to go to 1, then wait for the scan to finish.
        await wait_for_value(
            self.status,
            ScanState.RUNNING,
            timeout=DEFAULT_TIMEOUT,
        )
        await wait_for_value(self.status, ScanState.DONE, timeout)


class ProgramAbort(Triggerable):
    """Abort a data collection by setting the PMAC string and then wait for the \
        status value to go back to 0.
    """

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        status_sig: SignalR,
    ) -> None:
        self.signal = pmac_str_sig
        self.status = status_sig

    @AsyncStatus.wrap
    async def trigger(self):
        await self.signal.set("A", wait=True)
        await sleep(1.0)  # TODO Check with scientist what this sleep is really for.
        await self.signal.set("P2401=0", wait=True)
        await wait_for_value(
            self.status,
            ScanState.DONE,
            timeout=DEFAULT_TIMEOUT,
        )


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

        self.enc_reset = PMACStringEncReset(
            self.pmac_string, backend=SoftSignalBackend(str)
        )

        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        # These next signals are readback values on PVARS which are set by the motion
        # program.
        self.scanstatus = epics_signal_r(float, "BL24I-MO-STEP-14:signal:P2401")
        self.counter = epics_signal_r(float, "BL24I-MO-STEP-14:signal:P2402")

        self.run_program = ProgramRunner(
            self.pmac_string, self.scanstatus, backend=SoftSignalBackend(str)
        )
        self.abort_program = ProgramAbort(self.pmac_string, self.scanstatus)

        super().__init__(name)
