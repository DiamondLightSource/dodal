from functools import cached_property

from ophyd_async.core import (
    Reference,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
)
from ophyd_async.core._device import DeviceVector
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.util.timestamp_recording_device import TimestampRecordingDevice


class TempSensorChannel(TimestampRecordingDevice):
    """A single temperature sensor channel on the mercury."""

    @cached_property
    def signal_to_timestamp(self) -> Reference[SignalR]:
        return Reference(self.readback)

    def __init__(self, prefix: str, name: str = "") -> None:

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, read_pv=f"{prefix}READ_TEMP_SIG_TEMP")

        super().__init__(name)


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
