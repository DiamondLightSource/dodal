from ophyd_async.core import Device, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class AcquireState(StrictEnum):
    DONE = "Done"
    ACQUIRE = "Acquire"


class Xspress3Channel(Device):
    """
    Xspress3 Channel contains the truncated detector data and its collection conditions
     including the definition of ROI(region of interest).
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.update_arrays = epics_signal_rw(AcquireState, prefix + "SCAS:TS:TSAcquire")

        self.roi_high_limit = epics_signal_rw(int, prefix + "SCA5_HLM")
        self.roi_low_limit = epics_signal_rw(int, prefix + "SCA5_LLM")
        self.time = epics_signal_r(int, prefix + "SCA0:Value_RBV")
        self.reset_ticks = epics_signal_r(int, prefix + "SCA1:Value_RBV")
        self.reset_count = epics_signal_r(int, prefix + "SCA2:Value_RBV")
        self.all_event = epics_signal_r(int, prefix + "SCA3:Value_RBV")
        self.all_good = epics_signal_r(int, prefix + "SCA4:Value_RBV")
        self.pileup = epics_signal_r(int, prefix + "SCA7:Value_RBV")
        self.total_time = epics_signal_r(int, prefix + "SCA8:Value_RBV")
        self.mca_roi1_LLM = epics_signal_r(int, prefix + "SCA8:Value_RBV")
        super().__init__(name=name)


class Xspress3ROIChannel(Device):
    """
    This is the Xspress3 multi-channel analyzer range
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.roi_start_x = epics_signal_rw(int, prefix + "MinX")
        self.roi_size_x = epics_signal_rw(int, prefix + "SizeX")
        super().__init__(name=name)
