from ophyd_async.core import (
    Device,
    Signal,
    SignalR,
    StandardReadable,
    derived_signal_r,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw_rbv,
    epics_signal_x,
)

from dodal.devices.fast_grid_scan import (
    GridScanParamsCommon,
    ZebraFastGridScan,
)
from dodal.log import LOGGER


class TwoDGridScanParams(GridScanParamsCommon):
    pass


def _create_soft_signal_and_set_to_zero(
    dtype: type[int | float], prefix: str
) -> SignalR:
    signal, _setter = soft_signal_r_and_setter(dtype, prefix)
    _setter(0)
    return signal


# Need to create motion controller too as PV for prog num doesnt exist
# It's okay though, we don't really need it
class MotionProgram(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.running = epics_signal_r(int, prefix + "PROGBITS")
        # Prog number PV doesn't exist for i02-1, but it's currently only used for logging
        self.program_number = soft_signal_r_and_setter(float, -1)
        super().__init__(name)


class TwoDFastGridScan(ZebraFastGridScan):
    """The EPICS interface for that 2D FGS's differs slightly from the standard
    Hyperion version: no Z steps or Z step size, exposure_time instead of dwell_time,
    no scan valid PV.

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
        self.position_counter = self._create_position_counter(prefix)

        # Z movement and second start position don't exist in EPICS for 2D scan.
        # Create soft signals for these so the class is structured like the common device.
        self.z_steps, _ = soft_signal_r_and_setter(int, 0)
        self.z_step_size, _ = soft_signal_r_and_setter(float, 0)
        self.z2_start, _ = soft_signal_r_and_setter(float, 0)
        # Should ask controls to add this PV
        self.scan_invalid = soft_signal_r_and_setter(float, 0)

        self.run_cmd = epics_signal_x(f"{prefix}RUN.PROC")
        self.status = epics_signal_r(int, f"{prefix}SCAN_STATUS")
        self.expected_images = derived_signal_r(
            self._calculate_expected_images,
            x=self.x_steps,
            y=self.y_steps,
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

        # Skip the FGSCommon init function as we have already overriden all the signals
        StandardReadable.__init__(self, name)

    async def _calculate_expected_images(self, x: int, y: int) -> int:
        LOGGER.info(f"Reading num of images found {x, y} images in each axis")
        return x * y


# todo: add test which checks this device has same signals as zebra one
# add test to use this device in the FGS and make sure it works
"""
def test_attributes_match(eggs_instance, other_instance):
    # Get attribute names of both instances
    eggs_attrs = set(vars(eggs_instance).keys())
    other_attrs = set(vars(other_instance).keys())

    # The attributes should be the same
    assert eggs_attrs == other_attrs, f"Attributes differ: {eggs_attrs} vs {other_attrs}"


    do another test to check datatypes of each signals are the same
"""
