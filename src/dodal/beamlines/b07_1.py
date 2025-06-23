from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.b07_1 import CCMC, B07CGrating, CCMCPositions
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b07-1")
PREFIX = BeamlinePrefix(BL, suffix="C")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def analyser_driver() -> SpecsAnalyserDriverIO:
    return SpecsAnalyserDriverIO(prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:")


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=B07CGrating)


@device_factory()
def ccmc() -> CCMC:
    return CCMC(prefix=f"{PREFIX.beamline_prefix}-OP-CCM-01:", positions=CCMCPositions)
