from enum import Enum

from numpy import float64
from numpy.typing import NDArray
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
    AcquireState,
    Xspress3Channel,
    Xspress3ROIChannel,
)
from dodal.log import LOGGER


class TriggerMode(str, Enum):
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    BURST = "Burst"
    TTL_Veto_Only = "TTL Veto Only"
    IDC = "IDC"
    SOTWARE_START_STOP = "Software Start/Stop"
    TTL_BOTH = "TTL Both"
    LVDS_VETO_ONLY = "LVDS Veto Only"
    LVDS_both = "LVDS Both"


class UpdateRBV(str, Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class AcquireRBVState(str, Enum):
    DONE = "Done"
    ACQUIRE = "Acquiring"


class DetectorState(str, Enum):
    IDLE = "Idle"
    ACQUIRE = "Acquire"
    READOUT = "Readout"
    CORRECT = "Correct"
    Saving = "Saving"
    ABORTING = "Aborting"
    ERROR = "Error"
    WAITING = "Waiting"
    INTILTIALIZING = "Initializing"
    DISCONNECTED = "Disconnected"
    ABORTED = "Aborted"


class Xspress3(Device):
    """Xpress/XpressMini is a region of interest (ROI) picker that sums the detector
    output into a scaler with user-defined regions. It is often used as a signal
     discriminator to provide better energy resolution in X-ray detection experiments.
     This currently only provide staging functionality.

    Parameters
    ----------
    prefix:
        Beamline part of PV
    name:
        Name of the device
    num_channels:
        Number of channel xspress3 has, default is 1 for mini.
    timeout:
        How long to wait for before timing out for staging/arming of detector default is 1 sec
    """

    def __init__(
        self, prefix: str, name: str = "", num_channels: int = 1, timeout=1
    ) -> None:
        self.channels = DeviceVector(
            {i: Xspress3Channel(f"{prefix}C{i}_") for i in range(1, num_channels + 1)}
        )
        """MCA on/off switch readback"""
        self.get_roi_calc_status = DeviceVector(
            {
                i: epics_signal_rw(float, f"{prefix}MCA{i}:Enable_RBV")
                for i in range(1, num_channels + 1)
            }
        )
        """start and size of the multi-channel analyzer (MCA) array"""
        self.roi_mca = DeviceVector(
            {
                i: Xspress3ROIChannel(f"{prefix}ROISUM{i}:")
                for i in range(1, num_channels + 1)
            }
        )

        """signal for the corrected MCA spectrum (1d array)"""
        self.dt_corrected_latest_mca = DeviceVector(
            {
                i: epics_signal_r(NDArray[float64], f"{prefix}ARR{i}:ArrayData")
                for i in range(1, num_channels + 1)
            }
        )

        """Shared controls for triggering detection"""
        self.timeout = timeout
        self.acquire_time = epics_signal_rw(float, prefix + "AcquireTime")
        self.max_num_channels = epics_signal_r(int, prefix + "MAX_NUM_CHANNELS_RBV")
        # acquire and acquire readback has a different enum
        self.acquire = epics_signal_rw(AcquireState, prefix + "Acquire")
        self.acquire_rbv = epics_signal_r(AcquireRBVState, prefix + "Acquire_RBV")
        self.trigger_mode = epics_signal_rw_rbv(TriggerMode, prefix + "TriggerMode")

        self.detector_state = epics_signal_r(
            DetectorState, prefix + "DetectorState_RBV"
        )

        self.set_num_images = epics_signal_rw(int, prefix + "NumImages")
        self.detector_busy_states = [
            DetectorState.ACQUIRE,
            DetectorState.CORRECT,
            DetectorState.ABORTING,
        ]
        super().__init__(name=name)

    async def stage(self) -> AsyncStatus:
        LOGGER.info("Arming Xspress3 detector...")
        await self.trigger_mode.set(TriggerMode.BURST)
        await wait_for_value(
            self.detector_state,
            lambda v: v in self.detector_busy_states,
            timeout=self.timeout,
        )
        await set_and_wait_for_value(
            self.acquire, AcquireState.ACQUIRE, timeout=self.timeout
        )
        return AsyncStatus(
            wait_for_value(self.acquire_rbv, AcquireRBVState.DONE, timeout=self.timeout)
        )
