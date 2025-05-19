from asyncio import sleep
from enum import Enum, IntEnum

from bluesky.protocols import Flyable, Movable, Triggerable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Device,
    Reference,
    SignalR,
    SignalRW,
    StandardReadable,
    observe_signals_value,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor

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
        self.signal_ref = Reference(pmac_str_sig)
        self.cmd_string = string_to_send

    @AsyncStatus.wrap
    async def trigger(self):
        await self.signal_ref().set(self.cmd_string, wait=True)


class PMACStringLaser(Device, Movable[LaserSettings]):
    """Set the pmac_string to control the laser."""

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        name: str = "",
    ) -> None:
        self._signal_ref = Reference(pmac_str_sig)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(
        self,
        value: LaserSettings,
    ):
        await self._signal_ref().set(value.value)


class PMACStringEncReset(Device, Movable[EncReset]):
    """Set a pmac_string to control the encoder channels in the controller."""

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        name: str = "",
    ) -> None:
        self._signal_ref = Reference(pmac_str_sig)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(
        self,
        value: EncReset,
    ):
        await self._signal_ref().set(value.value)


class ProgramRunner(Device, Flyable):
    """Run the collection by setting the program number on the PMAC string.

    Once the program number has been set, wait for the collection to be complete.
    This will only be true when the status becomes 0.
    """

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        status_sig: SignalR,
        counter_sig: SignalR,
        prog_num_sig: SignalRW,
        counter_time_sig: SignalRW,
        name: str = "",
    ) -> None:
        self._signal_ref = Reference(pmac_str_sig)
        self._status_ref = Reference(status_sig)
        self._counter_ref = Reference(counter_sig)
        self._prog_num_ref = Reference(prog_num_sig)
        self._counter_time_ref = Reference(counter_time_sig)

        super().__init__(name)

    async def _get_prog_number_string(self) -> str:
        prog_num = await self._prog_num_ref().get_value()
        return f"&2b{prog_num}r"

    @AsyncStatus.wrap
    async def kickoff(self):
        """Kick off the collection by sending a program number to the pmac_string and \
            wait for the scan status PV to go to 1.
        """
        prog_num_str = await self._get_prog_number_string()
        await self._signal_ref().set(prog_num_str, wait=True)
        await wait_for_value(
            self._status_ref(),
            ScanState.RUNNING,
            timeout=DEFAULT_TIMEOUT,
        )

    @AsyncStatus.wrap
    async def complete(self):
        """Stop collecting when the scan status PV goes to 0 or when counter PV hasn't \
            updated for 30 seconds.
        """
        counter_time = await self._counter_time_ref().get_value()
        async for signal, value in observe_signals_value(
            self._status_ref(),
            self._counter_ref(),
            timeout=counter_time,
        ):
            if signal is self._status_ref():
                if value == ScanState.DONE:
                    break


class ProgramAbort(Triggerable):
    """Abort a data collection by setting the PMAC string and then wait for the \
        status value to go back to 0.
    """

    def __init__(
        self,
        pmac_str_sig: SignalRW,
        status_sig: SignalR,
    ) -> None:
        self._signal_ref = Reference(pmac_str_sig)
        self._status_ref = Reference(status_sig)

    @AsyncStatus.wrap
    async def trigger(self):
        await self._signal_ref().set("A", wait=True)
        await sleep(1.0)  # TODO Check with scientist what this sleep is really for.
        await self._signal_ref().set("P2401=0", wait=True)
        await wait_for_value(
            self._status_ref(),
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

        self.laser = PMACStringLaser(self.pmac_string)

        self.enc_reset = PMACStringEncReset(
            self.pmac_string,
        )

        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        # These next signals are readback values on PVARS which are set by the motion
        # program.
        self.scanstatus = epics_signal_r(float, "BL24I-MO-STEP-14:signal:P2401")
        self.counter = epics_signal_r(float, "BL24I-MO-STEP-14:signal:P2402")

        # A couple of soft signals for running a collection: program number to send to
        # the PMAC_STRING and expected collection time.
        self.program_number = soft_signal_rw(int)
        self.counter_time = soft_signal_rw(float, initial_value=30.0, units="s")

        self.run_program = ProgramRunner(
            self.pmac_string,
            self.scanstatus,
            self.counter,
            self.program_number,
            self.counter_time,
        )
        self.abort_program = ProgramAbort(self.pmac_string, self.scanstatus)

        super().__init__(name)
