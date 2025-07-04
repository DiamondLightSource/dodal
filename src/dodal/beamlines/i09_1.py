from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.i09.dcm import DCM
from dodal.devices.i09_1 import LensMode
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-1")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def dcm() -> DCM:
    return DCM(prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:")


@device_factory()
def analyser_driver() -> SpecsAnalyserDriverIO[LensMode]:
    return SpecsAnalyserDriverIO[LensMode](
        f"{PREFIX.beamline_prefix}-EA-DET-02:CAM:",
        LensMode,
        {"source1": dcm().energy_in_ev},
    )
