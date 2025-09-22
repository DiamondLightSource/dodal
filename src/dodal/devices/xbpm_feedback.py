from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, Device, Reference, StrictEnum, observe_value
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.device_utils import periodic_reminder
from dodal.devices.baton import Baton
from dodal.log import LOGGER


class Pause(StrictEnum):
    PAUSE = "Paused"  # 0
    RUN = "Ok to Run"  # 1


class XBPMFeedback(Device, Triggerable):
    """The XBPM feedback device is an IOC that moves the DCM, HFM and VFM to automatically
    hold the beam into place, as measured by the XBPM sensor."""

    def __init__(self, prefix: str, name: str = "", baton: Baton | None = None) -> None:
        self.pos_ok = epics_signal_r(float, prefix + "XBPM2POSITION_OK")
        self.pos_stable = epics_signal_r(float, prefix + "XBPM2_STABLE")
        self.pause_feedback = epics_signal_rw(Pause, prefix + "FB_PAUSE")
        self.baton_ref = Reference(baton) if baton else None
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def trigger(self):
        if self.baton_ref and await self.baton_ref().commissioning.get_value():
            LOGGER.warning("Commissioning mode enabled, ignoring feedback")
        else:
            async with periodic_reminder("Waiting for XBPM"):
                async for value in observe_value(self.pos_stable):
                    if value:
                        return
