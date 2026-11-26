from functools import cached_property

from ophyd_async.core import SignalR, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.util.timestamp_recording_device import TimestampRecordingDevice


class SimplePanda(TimestampRecordingDevice):
    """This is a simple implementation of the panda that just sends one trigger and
    records the timestamp of the trigger.

    This should be done with the actual panda device,
    see https://github.com/DiamondLightSource/crystallography-bluesky/issues/218
    """

    @cached_property
    def _signal_to_timestamp(self) -> SignalR:
        return self._trigger

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self._trigger = epics_signal_rw(bool, read_pv=f"{prefix}BITS:A")
            self.pulse_width = epics_signal_rw(float, read_pv=f"{prefix}PULSE1:WIDTH")
        super().__init__(name)
