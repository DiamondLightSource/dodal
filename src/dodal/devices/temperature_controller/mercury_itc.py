from copy import deepcopy

from bluesky.protocols import Reading
from event_model import DataKey
from ophyd_async.core import StandardReadable, StandardReadableFormat
from ophyd_async.core._device import DeviceVector
from ophyd_async.core._utils import merge_gathered_dicts
from ophyd_async.epics.core import epics_signal_r


class TempSensorChannel(StandardReadable):
    """A single temperature sensor channel on the mercury."""

    def __init__(self, prefix: str, name: str = "") -> None:

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, read_pv=f"{prefix}READ_TEMP_SIG_TEMP")

        super().__init__(name=name)

    async def describe(self) -> dict[str, DataKey]:
        """Adds a new signal on a device that is just the timestamp of readings from an
        existing signal.

        This is a workaround so that the nexus writer will actually record the timestamp.
        """
        descriptions = await merge_gathered_dicts(
            [func() for func in self._describe_funcs]
        )
        descriptions[f"{self.readback.name}-timestamp"] = deepcopy(
            descriptions[self.readback.name]
        )
        descriptions[f"{self.readback.name}-timestamp"]["dtype"] = "number"
        return descriptions

    async def read(self) -> dict[str, Reading]:
        """Reads the values from the device, adding a new signal for the timestamp of
        the readback.

        This is a workaround so that the nexus writer will actually record the timestamp.
        """
        readings = await merge_gathered_dicts([func() for func in self._read_funcs])
        readings[f"{self.readback.name}-timestamp"] = deepcopy(
            readings[self.readback.name]
        )
        readings[f"{self.readback.name}-timestamp"]["value"] = readings[
            f"{self.readback.name}-timestamp"
        ]["timestamp"]
        return readings


class MercuryITC(StandardReadable):
    """Device for controlling and reading from a MercuryITC temperature controller.

    Args:
        prefix (str): The EPICS prefix for the Mercury device.
        name (str, optional): Name for the device.
    """

    def __init__(self, prefix: str, name: str = "", number_of_channels=3):
        with self.add_children_as_readables():
            self.sensors: DeviceVector[TempSensorChannel] = DeviceVector(
                {
                    i: TempSensorChannel(prefix=f"{prefix}TEMP{i}:")
                    for i in range(1, number_of_channels + 1)
                }
            )

        super().__init__(name=name)
