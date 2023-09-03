from ophyd import Component, Device, EpicsSignalRO, EpicsSignal


class XBPMFeedback(Device):
    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pause: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")
