from collections import OrderedDict
from typing import Dict, Sequence

from bluesky.protocols import Descriptor, Reading
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r


class IndexingReadable(StandardReadable):
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
        pv_reading["value"] = pv_reading["value"][self.index]
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


class BartRobot(StandardReadable):
    """The sample changing robot."""

    def __init__(
        self,
        name: str,
        prefix: str,
    ) -> None:
        self.barcode = IndexingReadable(prefix + "BARCODE")
        self.gonio_pin_sensor = epics_signal_r(bool, "PIN_MOUNTED")
        super().__init__(name=name)
