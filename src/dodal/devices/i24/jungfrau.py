from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO


class JungfrauM1(Device):
    acquire_period_s: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:AcquirePeriod")
    exposure_time_s: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:ExposureTime")
    acquire_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Acquire_RBV")
    state_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:State_RBV")
    writing_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Writing_RBV")
    acquire_start: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:Acquire")
    clear_error: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:ClearError")
    frames_written_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:FramesWritten_RBV")
    frame_count: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:FrameCount")
    gain_mode: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:GainMode")
    error_rbv: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Error_RBV", string=True)
    file_directory: EpicsSignal = Cpt(
        EpicsSignal, "Jungfrau:FileDirectory", string=True
    )
