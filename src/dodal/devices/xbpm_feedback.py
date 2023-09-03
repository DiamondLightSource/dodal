from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import StableSubscriptionStatus, StatusBase


class XBPMFeedback(Device):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    # The time that the feedback needs to be high to be considered stable
    STABILITY_TIME = 3

    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pause_feedback: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")

    def trigger(self) -> StatusBase:
        status = StableSubscriptionStatus(
            self.pos_ok,
            lambda value, *args, **kwargs: value == 1,
            self.STABILITY_TIME,
            timeout=60,
        )

        if self.pos_ok.get() == 1:
            status.set_finished()
        return status
