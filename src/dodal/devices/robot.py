import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Sequence

from bluesky.protocols import Descriptor, Movable, Reading
from ophyd_async.core import AsyncStatus, StandardReadable, observe_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_x

from dodal.devices.util.epics_util import epics_signal_rw_rbv
from dodal.log import LOGGER


class SingleIndexWaveformReadable(StandardReadable):
    """Wraps a waveform PV that contains a list of strings into a device where only one
    of them is returned when read.
    """

    def __init__(
        self,
        pv: str,
        name="",
        index: int = 0,
    ) -> None:
        """
        Args:
            pv (str): The waveform PV that contains a list of strings
            index (int, optional): The index to read. Defaults to 0.
        """
        self.bare_signal = epics_signal_r(Sequence[str], pv)
        self.index = index
        super().__init__(name=name)

    async def read(self) -> Dict[str, Reading]:
        underlying_read = await self.bare_signal.read()
        pv_reading = underlying_read[self.bare_signal.name]
        pv_reading["value"] = str(pv_reading["value"][self.index])
        return OrderedDict([(self._name, pv_reading)])

    async def describe(self) -> dict[str, Descriptor]:
        desc = OrderedDict(
            [
                (
                    self._name,
                    (await self.bare_signal.describe())[self.bare_signal.name],
                )
            ],
        )
        return desc


@dataclass
class SampleLocation:
    puck: int
    pin: int


class BartRobot(StandardReadable, Movable):
    """The sample changing robot."""

    LOAD_TIMEOUT = 60

    def __init__(
        self,
        name: str,
        prefix: str,
    ) -> None:
        self.barcode = SingleIndexWaveformReadable(prefix + "BARCODE")
        self.gonio_pin_sensor = epics_signal_r(bool, prefix + "PIN_MOUNTED")
        self.next_pin = epics_signal_rw_rbv(int, prefix + "NEXT_PIN")
        self.next_puck = epics_signal_rw_rbv(int, prefix + "NEXT_PUCK")
        self.load = epics_signal_x(prefix + "LOAD.PROC")
        self.program_running = epics_signal_r(bool, prefix + "PROGRAM_RUNNING")
        super().__init__(name=name)

    async def _load_pin_and_puck(self, sample_location: SampleLocation):
        LOGGER.info(f"Loading pin {sample_location}")
        async for value in observe_value(self.program_running):
            if not value:
                break
            LOGGER.info("Waiting on robot program to finish")
        await asyncio.gather(
            self.next_puck.set(sample_location.puck),
            self.next_pin.set(sample_location.pin),
        )
        await self.load.trigger()

    def set(self, sample_location: SampleLocation) -> AsyncStatus:
        return AsyncStatus(
            asyncio.wait_for(
                self._load_pin_and_puck(sample_location), timeout=self.LOAD_TIMEOUT
            )
        )
