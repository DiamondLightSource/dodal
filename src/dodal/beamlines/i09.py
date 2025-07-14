from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.devices.i09 import DCM, Grating, LensMode
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def pgm() -> PGM:
    return PGM(
        prefix=f"{BeamlinePrefix(BL, suffix='J').beamline_prefix}-MO-PGM-01:",
        grating=Grating,
    )


@device_factory()
def dcm() -> DCM:
    return DCM(prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:")


@device_factory()
def analyser_driver() -> VGScientaAnalyserDriverIO[LensMode]:
    energy_sources = {
        "source1": pgm().energy.user_readback,
        "source2": dcm().energy_in_ev,
    }
    return VGScientaAnalyserDriverIO[LensMode](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        energy_sources=energy_sources,
    )
