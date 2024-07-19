import asyncio
from asyncio import FIRST_COMPLETED, Task
from dataclasses import dataclass
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    set_and_wait_for_value,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_x
from ophyd_async.epics.signal.signal import epics_signal_rw_rbv

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


class PinMounted(str, Enum):
    NO_PIN_MOUNTED = "No Pin Mounted"
    PIN_MOUNTED = "Pin Mounted"


class BartRobot(StandardReadable, Movable):
    """The sample changing robot."""

    LOAD_TIMEOUT = 60
    NO_PIN_ERROR_CODE = 25

    def __init__(
        self,
        name: str,
        prefix: str,
    ) -> None:
        self.barcode = epics_signal_r(str, prefix + "BARCODE")
        self.gonio_pin_sensor = epics_signal_r(PinMounted, prefix + "PIN_MOUNTED")
        self.next_pin = epics_signal_rw_rbv(float, prefix + "NEXT_PIN")
        self.next_puck = epics_signal_rw_rbv(float, prefix + "NEXT_PUCK")
        self.next_sample_id = epics_signal_rw_rbv(float, prefix + "NEXT_ID")
        self.sample_id = epics_signal_r(float, prefix + "CURRENT_ID_RBV")
        self.load = epics_signal_x(prefix + "LOAD.PROC")
        self.program_running = epics_signal_r(bool, prefix + "PROGRAM_RUNNING")
        self.program_name = epics_signal_r(str, prefix + "PROGRAM_NAME")
        self.error_str = epics_signal_r(str, prefix + "PRG_ERR_MSG")
        # Change error_code to int type when https://github.com/bluesky/ophyd-async/issues/280 released
        self.error_code = epics_signal_r(float, prefix + "PRG_ERR_CODE")
        super().__init__(name=name)

    async def pin_mounted_or_no_pin_found(self):
        """This co-routine will finish when either a pin is detected or the robot gives
        an error saying no pin was found (whichever happens first). In the case where no
        pin was found a RobotLoadFailed error is raised.
        """

        async def raise_if_no_pin():
            await wait_for_value(self.error_code, self.NO_PIN_ERROR_CODE, None)
            raise RobotLoadFailed(self.NO_PIN_ERROR_CODE, "Pin was not detected")

        finished, unfinished = await asyncio.wait(
            [
                Task(raise_if_no_pin()),
                Task(
                    wait_for_value(self.gonio_pin_sensor, PinMounted.PIN_MOUNTED, None)
                ),
            ],
            return_when=FIRST_COMPLETED,
        )
        for task in unfinished:
            task.cancel()
        for task in finished:
            await task

    async def _load_pin_and_puck(self, sample_location: SampleLocation):
        LOGGER.info(f"Loading pin {sample_location}")
        if await self.program_running.get_value():
            LOGGER.info(
                f"Waiting on robot to finish {await self.program_name.get_value()}"
            )
            await wait_for_value(self.program_running, False, None)
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
    async def set(self, sample_location: SampleLocation):
        try:
            await asyncio.wait_for(
                self._load_pin_and_puck(sample_location), timeout=self.LOAD_TIMEOUT
            )
        except asyncio.TimeoutError:
            error_code = await self.error_code.get_value()
            error_string = await self.error_str.get_value()
            raise RobotLoadFailed(error_code, error_string)
