from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class XBPMFeedback(Device):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pause_feedback: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")
