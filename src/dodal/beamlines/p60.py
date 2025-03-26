from dodal.common.beamlines.beamline_utils import (
    BL,
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.vgscienta_analyser import (
    VGScientaAnalyserController,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p60")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def r4000() -> VGScientaAnalyserController:
    """Get a read-only attenuator device for i24, instantiate it if it hasn't already
    been. If this is called when already instantiated in i24, it will return the
    existing object."""
    return VGScientaAnalyserController(
        f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        "r4000",
    )
