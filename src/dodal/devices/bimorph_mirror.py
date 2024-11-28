from typing import Annotated as A

from bluesky.protocols import Movable
from ophyd_async.core import SignalR, StandardReadable
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import PvSuffix, epics_signal_r


class BimorphMirrorChannel(StandardReadable):
    vout_rbv: A[SignalR[float], PvSuffix("VOUT_RBV"), Format.HINTED_SIGNAL]


class BimorphMirror(StandardReadable, Movable):
    def __init__(self, prefix: str, name="", number_of_channels: int = 0):
        self.number_of_channels = number_of_channels

        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self._vout_rbv_channels = [
                epics_signal_r(float, prefix + "C" + str(i + 1) + ":VOUT_RBV")
                for i in range(number_of_channels)
            ]
