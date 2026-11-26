from abc import abstractmethod
from copy import deepcopy
from functools import cached_property

from bluesky.protocols import Reading
from event_model import DataKey
from ophyd_async.core import Reference, SignalR, StandardReadable
from ophyd_async.core._utils import merge_gathered_dicts


class TimestampRecordingDevice(StandardReadable):
    """A device that records the timestamp of readings from an existing signal.

    This is required as the nexus writer currently does not record timestamps unless
    they are new individual signals.
    """

    @cached_property
    @abstractmethod
    def signal_to_timestamp(self) -> Reference[SignalR]:
        """Reference to the signal whose timestamp should be recorded."""

    async def describe(self) -> dict[str, DataKey]:
        """Adds a new signal on a device that is just the timestamp of readings from an
        existing signal.

        This is a workaround so that the nexus writer will actually record the timestamp.
        """
        descriptions = await merge_gathered_dicts(
            [func() for func in self._describe_funcs]
        )
        descriptions[f"{self.signal_to_timestamp().name}-timestamp"] = deepcopy(
            descriptions[self.signal_to_timestamp().name]
        )
        descriptions[f"{self.signal_to_timestamp().name}-timestamp"]["dtype"] = "number"
        return descriptions

    async def read(self) -> dict[str, Reading]:
        """Reads the values from the device, adding a new signal for the timestamp of
        the readback.

        This is a workaround so that the nexus writer will actually record the timestamp.
        """
        readings = await merge_gathered_dicts([func() for func in self._read_funcs])
        readings[f"{self.signal_to_timestamp().name}-timestamp"] = deepcopy(
            readings[self.signal_to_timestamp().name]
        )
        readings[f"{self.signal_to_timestamp().name}-timestamp"]["value"] = readings[
            f"{self.signal_to_timestamp().name}-timestamp"
        ]["timestamp"]
        return readings
