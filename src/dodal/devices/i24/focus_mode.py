from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw

# BL24I-OP-MFM-01:G1:TARGETAPPLY


class FocusMode(str, Enum):
    focus10 = "HMFMfocus10"
    # NOTE TODO This would be VMFMfocus10 for vertical


class MirrorFocusMode(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.horizontal = epics_signal_rw(FocusMode, prefix + "G1:TARGETAPPLY")
        self.vertical = epics_signal_rw(FocusMode, prefix + "G0:TARGETAPPLY")
        super().__init__(name)
