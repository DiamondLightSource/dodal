from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i19.hutch_access import ACCESS_DEVICE_NAME, HutchAccessControl
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "i19-optics"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def shutter() -> HutchShutter:
    """Get the i19 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return HutchShutter(
        f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        "shutter",
    )


@device_factory()
def access_control() -> HutchAccessControl:
    """Get a device that checks the active hutch for i19, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return HutchAccessControl(
        f"{PREFIX.beamline_prefix}-OP-STAT-01:", ACCESS_DEVICE_NAME
    )
