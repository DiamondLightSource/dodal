from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import StatusBase, SubscriptionStatus


class XBPMFeedback(Device):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    # Values to set to pause_feedback
    PAUSE = 0
    RUN = 1

    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pos_stable: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2_STABLE")
    pause_feedback: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")

    def trigger(self) -> StatusBase:
        return SubscriptionStatus(
            self.pos_stable, lambda *, old_value, value, **kwargs: value == 1
        )


class XBPMFeedbackI04(Device):
    """The I04 version of this device has a slightly different trigger method"""

    # Values to set to pause_feedback
    PAUSE = 0
    RUN = 1

    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pause_feedback: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")

    def trigger(self) -> StatusBase:
        return SubscriptionStatus(
            self.pos_ok,
            lambda *, old_value, value, **kwargs: value == 1,
            timeout=60,
        )
