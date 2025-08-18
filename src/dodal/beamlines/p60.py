from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser import SelectedSource
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.devices.p60 import (
    LabXraySource,
    LabXraySourceReadable,
    LensMode,
    PassEnergy,
    PsuMode,
)
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


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/P60-13
@device_factory()
def analyser_driver() -> VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]:
    energy_sources = {
        SelectedSource.SOURCE1: al_kalpha_source().energy_ev,
        SelectedSource.SOURCE2: mg_kalpha_source().energy_ev,
    }
    return VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        pass_energy_type=PassEnergy,
        energy_sources=energy_sources,
    )
