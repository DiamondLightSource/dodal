from ophyd_async.core import Reference, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.util.timestamp_recording_device import TimestampRecordingDevice


class SimplePanda(TimestampRecordingDevice):
    """This is a simple implementation of the panda that just sends one trigger and
    records the timestamp of the trigger.

    This should be done with the actual panda device,
    see https://github.com/DiamondLightSource/crystallography-bluesky/issues/218
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self._trigger = epics_signal_rw(bool, read_pv=f"{prefix}BITS:A")
            self.pulse_width = epics_signal_rw(float, read_pv=f"{prefix}PULSE1:WIDTH")
        super().__init__(Reference(self._trigger), name=name)
