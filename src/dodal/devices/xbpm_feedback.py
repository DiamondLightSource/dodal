from enum import Enum

import ophyd
from bluesky.protocols import Triggerable
from ophyd import Component, EpicsSignal, EpicsSignalRO
from ophyd.status import StatusBase, SubscriptionStatus
from ophyd_async.core import Device, observe_value
from ophyd_async.core.async_status import AsyncStatus
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class Pause(str, Enum):
    PAUSE = "Paused"  # 0
    RUN = "Ok to Run"  # 1


class XBPMFeedback(Device, Triggerable):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    def __init__(self, prefix: str = "", name: str = "xbpm_feedback") -> None:
        self.pos_ok = epics_signal_r(float, prefix + "-EA-FDBK-01:XBPM2POSITION_OK")
        self.pos_stable = epics_signal_r(float, prefix + "-EA-FDBK-01:XBPM2_STABLE")
        self.pause_feedback = epics_signal_rw(Pause, prefix + "-EA-FDBK-01:FB_PAUSE")
        self.x = epics_signal_r(float, prefix + "-EA-XBPM-02:PosX:MeanValue_RBV")
        self.y = epics_signal_r(float, prefix + "-EA-XBPM-02:PosY:MeanValue_RBV")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def trigger(self):
        async for value in observe_value(self.pos_stable):
            if value:
                return


class XBPMFeedbackI04(ophyd.Device):
    """The I04 version of this device has a slightly different trigger method"""

    # Values to set to pause_feedback
    PAUSE = 0
    RUN = 1

    pos_ok = Component(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    pause_feedback = Component(EpicsSignal, "-EA-FDBK-01:FB_PAUSE")
    x = Component(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y = Component(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")

    def trigger(self) -> StatusBase:
        return SubscriptionStatus(
            self.pos_ok,
            lambda *, old_value, value, **kwargs: value == 1,
            timeout=60,
        )
