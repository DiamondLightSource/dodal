from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import StatusBase, SubscriptionStatus


class XBPMFeedback(Device):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    # We need to wait for the beam to be locked into position for this amount of time
    # until we are certain that it is stable.
    STABILITY_TIME = 3

    pos_ok: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pos_stable: EpicsSignalRO = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2_STABLE")
    pause_feedback: EpicsSignal = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")

    def trigger(self) -> StatusBase:
        return SubscriptionStatus(
            self.pos_stable,
            lambda *, old_value, value, **kwargs: value == 1,
            timeout=60,
        )
