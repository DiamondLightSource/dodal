from enum import IntEnum

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal


class TriggerMode(IntEnum):
    SOFTWARE = 0
    HARDWARE = 1


class JungfrauM1(Device):
    trigger_mode = Cpt(EpicsSignal, "Timing")
    trigger_count = Cpt(EpicsSignal, "TriggerCount")
    acquire_period_s = Cpt(EpicsSignal, "AcquirePeriod")
    exposure_time_s = Cpt(EpicsSignal, "ExposureTime")
    acquire_rbv = Cpt(EpicsSignal, "Acquire_RBV")
    state_rbv = Cpt(EpicsSignal, "State_RBV")
    writing_rbv = Cpt(EpicsSignal, "Writing_RBV")
    acquire_start = Cpt(EpicsSignal, "Acquire")
    clear_error = Cpt(EpicsSignal, "ClearError")
    frames_written_rbv = Cpt(EpicsSignal, "FramesWritten_RBV")
    frame_count = Cpt(EpicsSignal, "FrameCount")
    gain_mode = Cpt(EpicsSignal, "GainMode", string=True)
    error_rbv = Cpt(EpicsSignal, "Error_RBV", string=True)
    file_directory = Cpt(EpicsSignal, "FileDirectory", string=True)
    file_name = Cpt(EpicsSignal, "FileName", string=True)
