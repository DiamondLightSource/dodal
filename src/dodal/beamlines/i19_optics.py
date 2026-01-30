from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i19.access_controlled.hutch_access import (
    ACCESS_DEVICE_NAME,
    HutchAccessControl,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "i19-optics"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def shutter() -> HutchShutter:
    """Real experiment shutter device for I19."""
    return HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")


@devices.factory()
def access_control() -> HutchAccessControl:
    """Device to check which hutch is the active hutch on i19."""
    return HutchAccessControl(
        f"{PREFIX.beamline_prefix}-OP-STAT-01:", ACCESS_DEVICE_NAME
    )
