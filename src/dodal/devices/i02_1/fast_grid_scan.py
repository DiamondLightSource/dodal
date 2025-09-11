import numpy as np
from ophyd_async.core import SignalR, derived_signal_r, soft_signal_r_and_setter
from ophyd_async.epics.core import epics_signal_rw_rbv
from pydantic import field_validator

from dodal.devices.fast_grid_scan import (
    FastGridScanCommon,
    GridScanParamsCommon,
    MotionProgram,
)
from dodal.log import LOGGER


class ZebraGridScanParamsTwoD(GridScanParamsCommon):
    exposure_time_ms: float = 213

    @field_validator("exposure_time_ms")
    @classmethod
    def non_integer_dwell_time(cls, exposure_time_ms: float) -> float:
        exposure_time_floor_rounded = np.floor(exposure_time_ms)
        exposure_time_is_close = np.isclose(
            exposure_time_ms, exposure_time_floor_rounded, rtol=1e-3
        )
        if not exposure_time_is_close:
            raise ValueError(
                f"Exposure time of {exposure_time_ms}ms is not an integer value. Fast Grid Scan only accepts integer values"
            )
        return exposure_time_ms


class ZebraFastGridScanTwoD(FastGridScanCommon[ZebraGridScanParamsTwoD]):
    """i02-1's EPICS interface for the 2D FGS differs slightly from the standard 3D
    version:
    - No Z steps, Z step sizes, or Y2 start positions, or Z2 start
    - No scan valid PV - see https://github.com/DiamondLightSource/mx-bluesky/issues/1203
    - No program_number - see https://github.com/DiamondLightSource/mx-bluesky/issues/1203
    """

    def __init__(
        self, prefix: str, motion_controller_prefix: str, name: str = ""
    ) -> None:
        full_prefix = prefix + "FGS:"
        super().__init__(full_prefix, motion_controller_prefix, name)

        # This signal could be put in the common device if the prefix gets standardised.
        # See https://github.com/DiamondLightSource/mx-bluesky/issues/1203
        self.exposure_time_ms = epics_signal_rw_rbv(
            float, f"{full_prefix}EXPOSURE_TIME"
        )

        self.movable_params["exposure_time_ms"] = self.exposure_time_ms

    def _create_expected_images_signal(self):
        return derived_signal_r(
            self._calculate_expected_images,
            x=self.x_steps,
            y=self.y_steps,
        )

    def _calculate_expected_images(self, x: int, y: int) -> int:
        LOGGER.info(f"Reading num of images found {x, y} images in each axis")
        return x * y

    # VMXm triggers the grid scan through GDA, which has its own validity check
    # so whilst this PV is being added, it isn't essential
    def _create_scan_invalid_signal(self, prefix: str) -> SignalR[float]:
        return soft_signal_r_and_setter(float, 0)[0]

    def _create_motion_program(self, motion_controller_prefix):
        return MotionProgram(motion_controller_prefix, has_prog_num=False)

    # To be standardised in https://github.com/DiamondLightSource/mx-bluesky/issues/1203
    def _create_position_counter(self, prefix: str):
        return epics_signal_rw_rbv(int, f"{prefix}POS_COUNTER")
