from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.specs_analyser_io import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b07")
PREFIX = BeamlinePrefix(BL, suffix="B")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def analyser_driver() -> SpecsAnalyserDriverIO:
    return SpecsAnalyserDriverIO(
        name="analyser_driver", prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:"
    )
