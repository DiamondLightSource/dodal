from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO


class JungfrauM1(Device):
    acquire_period_s: EpicsSignal = Cpt(EpicsSignal, "AcquirePeriod")
    exposure_time_s: EpicsSignal = Cpt(EpicsSignal, "ExposureTime")
    acquire_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Acquire_RBV")
    state_rbv: EpicsSignalRO = Cpt(EpicsSignal, "State_RBV")
    writing_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Writing_RBV")
    acquire_start: EpicsSignal = Cpt(EpicsSignal, "Acquire")
    clear_error: EpicsSignal = Cpt(EpicsSignal, "ClearError")
    frames_written_rbv: EpicsSignalRO = Cpt(EpicsSignal, "FramesWritten_RBV")
    frame_count: EpicsSignal = Cpt(EpicsSignal, "FrameCount")
    gain_mode: EpicsSignal = Cpt(EpicsSignal, "GainMode")
    error_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Error_RBV", string=True)
    file_directory: EpicsSignal = Cpt(EpicsSignal, "FileDirectory", string=True)
