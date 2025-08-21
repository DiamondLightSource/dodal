from ophyd_async.core import Device, SignalR, derived_signal_r, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.fast_grid_scan import (
    FastGridScanCommon,
    ZebraGridScanParams,
)
from dodal.log import LOGGER


class MotionProgram(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.running = epics_signal_r(int, prefix + "PROGBITS")
        # Prog number PV doesn't exist for i02-1, but it's currently only used for logging
        self.program_number, _ = soft_signal_r_and_setter(float, -1)
        super().__init__(name)


# TODO this needs to contain differences between 3d and 2d, and those differences need to be taken out
# of common and confirm that we don't refer to those signals at the plan level.
class TwoDGridScanNew(FastGridScanCommon[ZebraGridScanParams]):
    def __init__(self, prefix: str, name: str = "") -> None:
        # Z movement and second start positions don't exist in EPICS for 2D scan.
        # Create soft signals for these so the class is structured like the common device.
        self.z_steps, _ = soft_signal_r_and_setter(int, 0)
        self.z_step_size, _ = soft_signal_r_and_setter(float, 0)
        self.z2_start, _ = soft_signal_r_and_setter(float, 0)
        self.y2_start, _ = soft_signal_r_and_setter(int, 0)


class ZebraTwoDFastGridScan(FastGridScanCommon[ZebraGridScanParams]):
    """The EPICS interface for the 2D FGS differs slightly from the standard
    version:
    - No Z steps, Z step sizes, or Y2 start positions, or Z2 start
    - No scan valid PV - see https://github.com/DiamondLightSource/mx-bluesky/issues/1203

    This device abstracts away the differences by adding empty signals to the missing PV's.
    Plans which expect the 3D grid scan device can then also use this.

    See https://github.com/DiamondLightSource/mx-bluesky/issues/1112 for long term solution
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        full_prefix = prefix + "FGS:"
        super().__init__(full_prefix, prefix, name)

    def _create_expected_images_signal(self):
        return derived_signal_r(
            self._calculate_expected_images,
            x=self.x_steps,
            y=self.y_steps,
        )

    def _calculate_expected_images(self, x: int, y: int) -> int:
        LOGGER.info(f"Reading num of images found {x, y} images in each axis")
        return x * y

    # VMXm will trigger the grid scan through GDA, which has its own validity check,
    # but this PV is being added: https://github.com/DiamondLightSource/mx-bluesky/issues/1203
    def _create_scan_invalid_signal(self, prefix: str) -> SignalR[float]:
        return soft_signal_r_and_setter(float, 0)[0]
