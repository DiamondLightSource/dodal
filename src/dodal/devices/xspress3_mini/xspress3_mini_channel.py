from enum import Enum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class TimeSeriesValues(Enum):
    START_VALUE = "Acquire"
    STOP_VALUE = "Done"
    UPDATE_VALUE = ""


class Xspress3MiniChannel(Device):
    update_arrays = Component(EpicsSignal, "SCAS:TS:TSAcquire")

    roi_high_limit = Component(EpicsSignal, "SCA5_HLM")
    roi_llm = Component(EpicsSignal, "SCA5_LLM")

    time = Component(EpicsSignalRO, "SCA0:Value_RBV")
    reset_ticks = Component(EpicsSignalRO, "SCA1:Value_RBV")
    reset_count = Component(EpicsSignalRO, "SCA2:Value_RBV")
    all_event = Component(EpicsSignalRO, "SCA3:Value_RBV")
    all_good = Component(EpicsSignalRO, "SCA4:Value_RBV")
    pileup = Component(EpicsSignalRO, "SCA7:Value_RBV")
    total_time = Component(EpicsSignalRO, "SCA8:Value_RBV")
