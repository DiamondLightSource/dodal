from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.devices.p60 import LabXraySource, LabXraySourceReadable
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p60")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def al_kalpha_source() -> LabXraySourceReadable:
    return LabXraySourceReadable(LabXraySource.AL_KALPHA)


@device_factory()
def mg_kalpha_source() -> LabXraySourceReadable:
    return LabXraySourceReadable(LabXraySource.MG_KALPHA)


@device_factory()
def analyser_driver() -> VGScientaAnalyserDriverIO:
    energy_sources = {
        "source1": al_kalpha_source().user_readback,
        "source2": mg_kalpha_source().user_readback,
    }
    return VGScientaAnalyserDriverIO(
        f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:", energy_sources
    )
