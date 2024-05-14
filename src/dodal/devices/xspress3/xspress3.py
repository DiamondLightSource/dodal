from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    Device,
    DeviceVector,
    set_and_wait_for_value,
    wait_for_value,
)
from ophyd_async.epics.signal.signal import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
)

from dodal.devices.xspress3.xspress3_channel import (
    Xspress3Channel,
    Xspress3ROIChannel,
)
from dodal.log import LOGGER


class TriggerMode(str, Enum):
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    BURST = "Burst"
    TTL_Veto_Only = "TTL_Veto_Only"
    IDC = "IDC"
    SOTWARE_START_STOP = "Software_Start/Stop"
    TTL_BOTH = "TTL_Both"
    LVDS_VETO_ONLY = "LVDS_Veto_Only"
    LVDS_both = "LVDS_Both"


class UpdateRBV(str, Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class EraseState(str, Enum):
    DONE = 0
    ERASE = 1


class AcquireState(str, Enum):
    DONE = 0
    ACQUIRE = 1


class DetectorState(str, Enum):
    ACQUIRE = "Acquire"
    CORRECT = "Correct"
    READOUT = "Readout"
    ABORTING = "Aborting"

    IDLE = "Idle"
    SAVING = "Saving"
    ERROR = "Error"
    INTILTIALIZING = "Initializing"
    DISCONNECTED = "Disconnected"
    ABORTED = "Aborted"


class Xspress3Mini(Device):
    """Xpress/XpressMini is a region of interest (ROI) picker that sums the detector
    output into a scaler with user-defined regions. It is often used as a signal
     discriminator to provide better energy resolution in X-ray detection experiments.
    """

    def __init__(self, prefix: str, name: str = "", num: int = 1, timeout=1) -> None:
        self.channels = DeviceVector(
            {i: Xspress3Channel(f"{prefix}:C{i}_") for i in range(1, num + 1)}
        )
        """MCA on/off switch"""
        self.get_roi_calc_status = DeviceVector(
            {
                i: epics_signal_rw(UpdateRBV, f"{prefix}:MCA{i}:Enable_RBV")
                for i in range(1, num + 1)
            }
        )
        """start and size of the MCA array"""
        self.roi_mca = DeviceVector(
            {i: Xspress3ROIChannel(f"{prefix}:ROISUM{i}:") for i in range(1, num + 1)}
        )

        """signal for the correct MCA spectrum (1d array)"""
        self.dt_corrected_latest_mca = DeviceVector(
            {
                i: epics_signal_r(float, f"{prefix}:ARR{i}:ArrayData")
                for i in range(1, num + 1)
            }
        )  # this is not float need fixing

        """Shared controls"""
        self.timeout = timeout
        self.acquire_time = epics_signal_rw(float, prefix + "AcquireTime")
        self.erase = epics_signal_rw(EraseState, prefix + "ERASE")
        self.max_num_channels = epics_signal_r(float, prefix + "MAX_NUM_CHANNELS_RBV")
        self.acquire = epics_signal_rw_rbv(AcquireState, prefix + "Acquire")

        self.trigger_mode = epics_signal_rw_rbv(TriggerMode, prefix + "TriggerMode")

        self.detector_state = epics_signal_r(
            DetectorState, prefix + "DetectorState_RBV"
        )

        self.set_num_images = epics_signal_rw(float, prefix + "NumImages")
        self.detector_busy_states = [
            DetectorState.ACQUIRE,
            DetectorState.CORRECT,
            DetectorState.ABORTING,
        ]
        super().__init__(name=name)

    async def stage(self) -> AsyncStatus:
        LOGGER.info("Arming Xspress3Mini detector...")
        await self.trigger_mode.set(TriggerMode.BURST)
        await wait_for_value(
            self.detector_state,
            lambda v: v in self.detector_busy_states,
            timeout=self.timeout,
        )
        await self.erase.set(EraseState.ERASE)
        await set_and_wait_for_value(
            self.acquire, AcquireState.ACQUIRE, timeout=self.timeout
        )
        return AsyncStatus(
            wait_for_value(self.acquire, AcquireState.DONE, timeout=self.timeout)
        )
