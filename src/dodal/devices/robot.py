import asyncio
from asyncio import FIRST_COMPLETED, CancelledError, Task, wait_for
from dataclasses import dataclass

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    StandardReadable,
    StrictEnum,
    set_and_wait_for_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw_rbv, epics_signal_x

from dodal.log import LOGGER


class RobotLoadFailed(Exception):
    error_code: int
    error_string: str

    def __init__(self, error_code: int, error_string: str) -> None:
        self.error_code, self.error_string = error_code, error_string
        super().__init__(error_string)

    def __str__(self) -> str:
        return self.error_string


@dataclass
class SampleLocation:
    puck: int
    pin: int


class PinMounted(StrictEnum):
    NO_PIN_MOUNTED = "No Pin Mounted"
    PIN_MOUNTED = "Pin Mounted"


class ErrorStatus(Device):
    def __init__(self, prefix: str) -> None:
        self.str = epics_signal_r(str, prefix + "_ERR_MSG")
        self.code = epics_signal_r(int, prefix + "_ERR_CODE")
        super().__init__()

    async def raise_if_error(self, raise_from: Exception):
        error_code = await self.code.get_value()
        if error_code:
            error_string = await self.str.get_value()
            raise RobotLoadFailed(int(error_code), error_string) from raise_from


class BartRobot(StandardReadable, Movable[SampleLocation]):
    """The sample changing robot."""

    # How long to wait for the robot if it is busy soaking/drying
    NOT_BUSY_TIMEOUT = 5 * 60

    # How long to wait for the actual load to happen
    LOAD_TIMEOUT = 60

    # Error codes that we do special things on
    NO_PIN_ERROR_CODE = 25
    LIGHT_CURTAIN_TRIPPED = 40

    # How far the gonio position can be out before loading will fail
    LOAD_TOLERANCE_MM = 0.02

    def __init__(self, name: str, prefix: str) -> None:
        self.barcode = epics_signal_r(str, prefix + "BARCODE")
        self.gonio_pin_sensor = epics_signal_r(PinMounted, prefix + "PIN_MOUNTED")

        self.next_pin = epics_signal_rw_rbv(float, prefix + "NEXT_PIN")
        self.next_puck = epics_signal_rw_rbv(float, prefix + "NEXT_PUCK")
        self.current_puck = epics_signal_r(float, prefix + "CURRENT_PUCK_RBV")
        self.current_pin = epics_signal_r(float, prefix + "CURRENT_PIN_RBV")

        self.next_sample_id = epics_signal_rw_rbv(int, prefix + "NEXT_ID")
        self.sample_id = epics_signal_r(int, prefix + "CURRENT_ID_RBV")

        self.load = epics_signal_x(prefix + "LOAD.PROC")
        self.program_running = epics_signal_r(bool, prefix + "PROGRAM_RUNNING")
        self.program_name = epics_signal_r(str, prefix + "PROGRAM_NAME")

        self.prog_error = ErrorStatus(prefix + "PRG")
        self.controller_error = ErrorStatus(prefix + "CNTL")

        self.reset = epics_signal_x(prefix + "RESET.PROC")
        super().__init__(name=name)

    async def pin_mounted_or_no_pin_found(self):
        """This co-routine will finish when either a pin is detected or the robot gives
        an error saying no pin was found (whichever happens first). In the case where no
        pin was found a RobotLoadFailed error is raised.
        """

        async def raise_if_no_pin():
            await wait_for_value(self.prog_error.code, self.NO_PIN_ERROR_CODE, None)
            raise RobotLoadFailed(self.NO_PIN_ERROR_CODE, "Pin was not detected")

        async def wfv():
            await wait_for_value(self.gonio_pin_sensor, PinMounted.PIN_MOUNTED, None)

        tasks = [
            (Task(raise_if_no_pin())),
            (Task(wfv())),
        ]
        try:
            finished, unfinished = await asyncio.wait(
                tasks,
                return_when=FIRST_COMPLETED,
            )
            for task in unfinished:
                task.cancel()
            for task in finished:
                await task
        except CancelledError:
            # If the outer enclosing task cancels after a timeout, this causes CancelledError to be raised
            # in the current task, when it propagates to here we should cancel all pending tasks before bubbling up
            for task in tasks:
                task.cancel()
            raise

    async def _load_pin_and_puck(self, sample_location: SampleLocation):
        if await self.controller_error.code.get_value() == self.LIGHT_CURTAIN_TRIPPED:
            LOGGER.info("Light curtain tripped, trying again")
            await self.reset.trigger()
        LOGGER.info(f"Loading pin {sample_location}")
        if await self.program_running.get_value():
            LOGGER.info(
                f"Waiting on robot to finish {await self.program_name.get_value()}"
            )
            await wait_for_value(
                self.program_running, False, timeout=self.NOT_BUSY_TIMEOUT
            )
        await asyncio.gather(
            set_and_wait_for_value(self.next_puck, sample_location.puck),
            set_and_wait_for_value(self.next_pin, sample_location.pin),
        )
        await self.load.trigger()
        if await self.gonio_pin_sensor.get_value() == PinMounted.PIN_MOUNTED:
            LOGGER.info("Waiting on old pin unloaded")
            await wait_for_value(self.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED, None)
        LOGGER.info("Waiting on new pin loaded")

        await self.pin_mounted_or_no_pin_found()

    @AsyncStatus.wrap
    async def set(self, value: SampleLocation):
        try:
            await wait_for(
                self._load_pin_and_puck(value),
                timeout=self.LOAD_TIMEOUT + self.NOT_BUSY_TIMEOUT,
            )
        except (asyncio.TimeoutError, TimeoutError) as e:
            # Will only need to catch asyncio.TimeoutError after https://github.com/bluesky/ophyd-async/issues/572
            await self.prog_error.raise_if_error(e)
            await self.controller_error.raise_if_error(e)
            raise RobotLoadFailed(0, "Robot timed out") from e
