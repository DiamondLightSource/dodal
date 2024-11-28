from bluesky.protocols import Movable
from ophyd_async.core import DeviceVector, StandardReadable
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import epics_signal_r


class BimorphMirrorChannel(StandardReadable):
    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.vout_rbv = epics_signal_r(float, f"{prefix}:VOUT_RBV")


class BimorphMirror(StandardReadable):
    def __init__(self, prefix: str, name="", number_of_channels: int = 0):
        self.number_of_channels = number_of_channels

        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.channels = DeviceVector(
                {
                    i: BimorphMirrorChannel(f"{prefix}:C{i}", f"channel{i}")
                    for i in range(1, number_of_channels + 1)
                }
            )
