from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO


class JungfrauM1(Device):
    AcquirePeriod: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:AcquirePeriod")
    ExposureTime: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:ExposureTime")
    Acquire_RBV: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Acquire_RBV")
    State_RBV: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:State_RBV")
    Writing_RBV: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Writing_RBV")
    Acquire: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:Acquire")
    ClearError: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:ClearError")
    FramesWritten_RBV: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:FramesWritten_RBV")
    FrameCount: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:FrameCount")
    GainMode: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:GainMode")
    Error_RBV: EpicsSignalRO = Cpt(EpicsSignal, "Jungfrau:Error_RBV")
    FileDirectory: EpicsSignal = Cpt(EpicsSignal, "Jungfrau:FileDirectory")
