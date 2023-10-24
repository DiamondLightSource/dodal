from asyncio import wait_for
from enum import Enum

from bluesky import RunEngine
from ophyd_async.core import AsyncStatus, Device, SignalR, SignalRW, wait_for_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class PauseFeedback(Enum):
    PAUSED = "Paused"
    OK = "Ok to Run"


class XBPMFeedback(Device):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    def __init__(self, prefix: str, name="") -> None:
        self.prefix = prefix
        # Values to set to pause_feedback
        self.PAUSE = 0
        self.RUN = 1
        self.pos_ok: SignalR = epics_signal_r(
            float, f"{self.prefix}-EA-FDBK-01:XBPM2POSITION_OK"
        )
        self.pause_feedback: SignalRW = epics_signal_rw(
            PauseFeedback, f"{self.prefix}-EA-FDBK-01:FB_PAUSE"
        )
        self.x: SignalR = epics_signal_r(
            float, f"{self.prefix}-EA-XBPM-02:PosX:MeanValue_RBV"
        )
        self.y: SignalR = epics_signal_r(
            float, f"{self.prefix}-EA-XBPM-02:PosY:MeanValue_RBV"
        )
        super().__init__(name)

    def trigger(self):
        return wait_for_value(
            self.pos_ok,
            1,
            timeout=60,
        )


class XBPMFeedbackI03(XBPMFeedback):
    """The XMBPM feedback on I03 has a pos_stable pv which it uses to trigger instead of pos_ok"""

    def __init__(self, prefix: str, name="") -> None:
        super().__init__(prefix, name)
        self.pos_stable: SignalR = epics_signal_r(
            float, f"{self.prefix}-EA-FDBK-01:XBPM2_STABLE"
        )

    @AsyncStatus.wrap
    async def trigger(self):
        return wait_for_value(
            self.pos_stable,
            1,
            timeout=60,
        )
