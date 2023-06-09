from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class Xspress3MiniChannel(Device):
    sca5_update_arrays_mini = Component(EpicsSignalRO, "SCAS:TS:TSAcquire")

    roi_high_limit = Component(EpicsSignal, "SCA5_HLM")
    roi_llm = Component(EpicsSignal, "SCA5_LLM")

    time = Component(EpicsSignalRO, "SCA:0:Value_RBV")
    reset_ticks = Component(EpicsSignalRO, "SCA:1:Value_RBV")
    reset_count = Component(EpicsSignalRO, "SCA:2:Value_RBV")
    all_event = Component(EpicsSignalRO, "SCA:3:Value_RBV")
    all_good = Component(EpicsSignalRO, "SCA:4:Value_RBV")
    pileup = Component(EpicsSignalRO, "SCA:7:Value_RBV")
    total_time = Component(EpicsSignalRO, "SCA:8:Value_RBV")
