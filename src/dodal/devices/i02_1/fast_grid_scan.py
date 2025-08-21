from ophyd_async.core import (
    Device,
    Signal,
    StandardReadable,
    derived_signal_r,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
    epics_signal_x,
)

from dodal.devices.fast_grid_scan import (
    ZebraFastGridScan,
)
from dodal.log import LOGGER


class MotionProgram(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.running = epics_signal_r(int, prefix + "PROGBITS")
        # Prog number PV doesn't exist for i02-1, but it's currently only used for logging
        self.program_number, _ = soft_signal_r_and_setter(float, -1)
        super().__init__(name)


class TwoDFastGridScan(ZebraFastGridScan):
    """The EPICS interface for the 2D FGS differs slightly from the standard
    version:
    - No Z steps, Z step sizes, or Y2 start positions,
    - Use exposure_time instead of dwell_time,
    - No scan valid PV - see https://github.com/DiamondLightSource/mx-bluesky/issues/1203

    This device abstracts away the differences by adding empty signals to the missing PV's.
    Plans which expect the 3D grid scan device can then also use this.

    See https://github.com/DiamondLightSource/mx-bluesky/issues/1112 for long term solution
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x_steps = epics_signal_rw_rbv(int, f"{prefix}X_NUM_STEPS")
        self.y_steps = epics_signal_rw_rbv(int, f"{prefix}Y_NUM_STEPS")
        self.x_step_size = epics_signal_rw_rbv(float, f"{prefix}X_STEP_SIZE")
        self.y_step_size = epics_signal_rw_rbv(float, f"{prefix}Y_STEP_SIZE")
        self.x_start = epics_signal_rw_rbv(float, f"{prefix}X_START")
        self.y1_start = epics_signal_rw_rbv(float, f"{prefix}Y_START")
        self.z1_start = epics_signal_rw_rbv(float, f"{prefix}Z_START")
        self.motion_program = MotionProgram("BL02J-MO-STEP-11:")

        # While the prefix is called exposure time, the motion script uses this value
        # to dwell on each trigger point - the names are interchangable here.
        self.dwell_time_ms = epics_signal_rw_rbv(float, f"{prefix}FGS:EXPOSURE_TIME")

        # Z movement and second start positions don't exist in EPICS for 2D scan.
        # Create soft signals for these so the class is structured like the common device.
        self.z_steps, _ = soft_signal_r_and_setter(int, 0)
        self.z_step_size, _ = soft_signal_r_and_setter(float, 0)
        self.z2_start, _ = soft_signal_r_and_setter(float, 0)
        self.y2_start, _ = soft_signal_r_and_setter(int, 0)

        # VMXm will trigger the grid scan through GDA, which has its own validity check,
        # but this PV is being added: https://github.com/DiamondLightSource/mx-bluesky/issues/1203
        self.scan_invalid = soft_signal_r_and_setter(float, 0)

        self.run_cmd = epics_signal_x(f"{prefix}RUN.PROC")
        self.stop_cmd = epics_signal_x(f"{prefix}FGS:STOP.PROC")
        self.status = epics_signal_r(int, f"{prefix}SCAN_STATUS")
        self.expected_images = derived_signal_r(
            self._calculate_expected_images, x=self.x_steps, y=self.y_steps, z=0
        )

        self.x_counter = epics_signal_r(int, f"{prefix}X_COUNTER")
        self.y_counter = epics_signal_r(int, f"{prefix}Y_COUNTER")

        # Kickoff timeout in seconds
        self.KICKOFF_TIMEOUT: float = 5.0

        self.COMPLETE_STATUS: float = 60.0

        self.movable_params: dict[str, Signal] = {
            "x_steps": self.x_steps,
            "y_steps": self.y_steps,
            "x_step_size_mm": self.x_step_size,
            "y_step_size_mm": self.y_step_size,
            "x_start_mm": self.x_start,
            "y1_start_mm": self.y1_start,
            "z1_start_mm": self.z1_start,
        }

        self.position_counter = self._create_position_counter(prefix)

        # Skip the FGSCommon init function as we have already overriden all the signals
        StandardReadable.__init__(self, name)

    def _create_position_counter(self, prefix: str):
        return epics_signal_rw(
            int, f"{prefix}POS_COUNTER", write_pv=f"{prefix}POS_COUNTER_WRITE"
        )

    def _calculate_expected_images(self, x: int, y: int, z: int) -> int:
        LOGGER.info(f"Reading num of images found {x, y} images in each axis")
        return x * y
