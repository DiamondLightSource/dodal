import asyncio
from dataclasses import dataclass
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, wait_for_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_x
from ophyd_async.epics.signal.signal import epics_signal_rw_rbv

from dodal.log import LOGGER


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
        super().__init__(name=name)

    async def _load_pin_and_puck(self, sample_location: SampleLocation):
        LOGGER.info(f"Loading pin {sample_location}")
        if await self.program_running.get_value():
            LOGGER.info(
                f"Waiting on robot to finish {await self.program_name.get_value()}"
            )
            await wait_for_value(self.program_running, False, None)
        await asyncio.gather(
            self.next_puck.set(sample_location.puck),
            self.next_pin.set(sample_location.pin),
        )
        await self.load.trigger()
        if await self.gonio_pin_sensor.get_value() == PinMounted.PIN_MOUNTED:
            LOGGER.info("Waiting on old pin unloaded")
            await wait_for_value(self.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED, None)
        LOGGER.info("Waiting on new pin loaded")
        await wait_for_value(self.gonio_pin_sensor, PinMounted.PIN_MOUNTED, None)

    def set(self, sample_location: SampleLocation) -> AsyncStatus:
        return AsyncStatus(
            asyncio.wait_for(
                self._load_pin_and_puck(sample_location), timeout=self.LOAD_TIMEOUT
            )
        )
