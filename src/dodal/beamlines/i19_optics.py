from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.devices.hutch_shutter import HutchShutter
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
