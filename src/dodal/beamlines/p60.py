from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p60")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def analyser_driver() -> VGScientaAnalyserDriverIO:
    return VGScientaAnalyserDriverIO(prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:")
