from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    Device,
    DeviceVector,
    Signal,
    set_and_wait_for_value,
    wait_for_value,
)
from ophyd_async.epics.signal.signal import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
)

from dodal.devices.ophyd_async_xspress3_mini.xspress3_mini_channel_oa import (
    Xspress3MiniChannel,
)

# ===========================================================================
from dodal.log import LOGGER


class AttenuationOptimisationFailedException(Exception):
    pass


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

    def __init__(self, prefix: str, name: str = "", num: int = 1) -> None:
        # Define some signals
        self.channels = DeviceVector(
            {i: Xspress3MiniChannel(f"{prefix}:C{i}") for i in range(1, num + 1)}
        )
        # self.channel_1 = Xspress3MiniChannel(prefix + "C1_")
        self.erase = epics_signal_rw(EraseState, prefix + "ERASE")
        self.get_max_num_channels = epics_signal_r(
            float, prefix + "MAX_NUM_CHANNELS_RBV"
        )
        self.acquire = epics_signal_rw_rbv(AcquireState, prefix + "Acquire")
        self.get_roi_calc_mini = epics_signal_rw(float, prefix + "MCA1:Enable_RBV")
        self.trigger_mode_mini = epics_signal_rw_rbv(
            TriggerMode, prefix + "TriggerMode"
        )
        self.roi_start_x = epics_signal_rw(float, prefix + "ROISUM1:MinX")
        self.roi_size_x = epics_signal_rw(float, prefix + "ROISUM1:SizeX")
        self.acquire_time = epics_signal_rw(float, prefix + "AcquireTime")
        self.detector_state = epics_signal_r(
            DetectorState, prefix + "DetectorState_RBV"
        )
        self.dt_corrected_latest_mca = epics_signal_r(float, prefix + "ARR1:ArrayData")
        self.set_num_images = epics_signal_rw(float, prefix + "NumImages")
        self.detector_busy_states = [
            DetectorState.ACQUIRE,
            DetectorState.CORRECT,
            DetectorState.ABORTING,
        ]
        super().__init__(name=name)

    async def stage(self):
        await self.arm()

    async def arm(self) -> AsyncStatus:
        LOGGER.info("Arming Xspress3Mini detector...")
        self.trigger_mode_mini.set(TriggerMode.BURST)
        await wait_for_value(
            self.detector_state, lambda v: v in self.detector_busy_states, timeout=1
        )
        self.erase.set(EraseState.ERASE)
        await set_and_wait_for_value(self.acquire, AcquireState.ACQUIRE, timeout=1)
        return AsyncStatus(wait_for_value(self.acquire, AcquireState.DONE, timeout=1))
