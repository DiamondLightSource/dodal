from enum import Enum

from ophyd_async.core import Device
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class TimeSeriesValues(str, Enum):
    START_VALUE = "Acquire"
    STOP_VALUE = "Done"
    UPDATE_VALUE = ""


class Xspress3MiniChannel(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        # Define some signals
        self.update_arrays = epics_signal_rw(float, prefix + "SCAS:TS:TSAcquire")

        self.roi_high_limit = epics_signal_rw(float, prefix + "SCA5_HLM")
        self.roi_llm = epics_signal_rw(float, prefix + "SCA5_LLM")

        self.time = epics_signal_r(float, prefix + "SCA0:Value_RBV")
        self.reset_ticks = epics_signal_r(float, prefix + "SCA1:Value_RBV")
        self.reset_count = epics_signal_r(float, prefix + "SCA2:Value_RBV")
        self.all_event = epics_signal_r(float, prefix + "SCA3:Value_RBV")
        self.all_good = epics_signal_r(float, prefix + "SCA4:Value_RBV")
        self.pileup = epics_signal_r(float, prefix + "SCA7:Value_RBV")
        self.total_time = epics_signal_r(float, prefix + "SCA8:Value_RBV")
        super().__init__(name=name)
