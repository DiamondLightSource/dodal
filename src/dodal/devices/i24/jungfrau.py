from enum import IntEnum

from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class TriggerMode(IntEnum):
    SOFTWARE = 0
    HARDWARE = 1


class BurstMode(IntEnum):
    ON = 1
    OFF = 0


class AcquireState(IntEnum):
    DONE = 0
    ACQUIRING = 1


class WriteState(IntEnum):
    DONE = 0
    WRITING = 1


class GainMode(StrictEnum):
    DYNAMIC = "dynamic"
    FORCESWITCHG1 = "forceswitchg1"
    FORCESWITCHG2 = "forceswitchg2"


# NOTE In the future, might want to switch this to standard detector?
# TODO Check all types!
class JungFrau1M(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.trigger_mode = epics_signal_rw(int, prefix + "Timing")
        self.trigger_count = epics_signal_rw(int, prefix + "TriggerCount")
        self.acquire_period_s = epics_signal_rw(float, prefix + "AcquirePeriod")
        self.exposure_time_s = epics_signal_rw(float, prefix + "ExposureTime")

        self.acquire_rbv = epics_signal_r(int, prefix + "Acquire_RBV")
        self.state_rbv = epics_signal_r(int, prefix + "State_RBV")
        self.writing_rbv = epics_signal_r(int, prefix + "Writing_RBV")
        self.acquire_start = epics_signal_rw(int, prefix + "Acquire")
        self.clear_error = epics_signal_rw(float, prefix + "ClearError")
        self.frames_written_rbv = epics_signal_r(int, prefix + "FramesWritten_RBV")
        self.frame_count = epics_signal_rw(int, prefix + "FrameCount")
        self.gain_mode = epics_signal_rw(GainMode, prefix + "GainMode")
        self.error_rbv = epics_signal_r(str, prefix + "Error_RBV")
        self.file_directory = epics_signal_rw(str, prefix + "FileDirectory")
        self.file_name = epics_signal_rw(str, prefix + "FileName")

        self.pedestal_mode = epics_signal_rw(int, prefix + "PedestalMode")
        self.pedestal_frames = epics_signal_rw(int, prefix + "PedestalFrames")
        self.pedestal_loops = epics_signal_rw(int, prefix + "PedestalLoops")

        self.burst_mode = epics_signal_rw(int, prefix + "BurstMode")
        self.power_state = epics_signal_rw(int, prefix + "PowerState")
        super().__init__(name)
