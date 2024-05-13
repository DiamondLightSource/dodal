from enum import Enum

from ophyd_async.core import Device
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class TimeSeriesValues(str, Enum):
    START_VALUE = "Acquire"
    STOP_VALUE = "Done"
    UPDATE_VALUE = ""


class Xspress3Channel(Device):
    """
    Xspress3 Channel contains the truncated detector data and its collection condition
     including the definition of ROI.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.update_arrays = epics_signal_rw(float, prefix + "SCAS:TS:TSAcquire")

        self.roi_high_limit = epics_signal_rw(float, prefix + "SCA5_HLM")
        self.roi_low_limit = epics_signal_rw(float, prefix + "SCA5_LLM")

        self.time = epics_signal_r(float, prefix + "SCA0:Value_RBV")
        self.reset_ticks = epics_signal_r(float, prefix + "SCA1:Value_RBV")
        self.reset_count = epics_signal_r(float, prefix + "SCA2:Value_RBV")
        self.all_event = epics_signal_r(float, prefix + "SCA3:Value_RBV")
        self.all_good = epics_signal_r(float, prefix + "SCA4:Value_RBV")
        self.pileup = epics_signal_r(float, prefix + "SCA7:Value_RBV")
        self.total_time = epics_signal_r(float, prefix + "SCA8:Value_RBV")
        super().__init__(name=name)


class Xspress3ROIChannel(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.roi_start_x = epics_signal_rw(float, prefix + "MinX")
        self.roi_size_x = epics_signal_rw(float, prefix + "SizeX")
        super().__init__(name=name)
