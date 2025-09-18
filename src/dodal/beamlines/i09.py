from dodal.beamlines.i09_1_shared import dcm
from dodal.beamlines.i09_2_shared import pgm
from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.electron_analyser import SelectedSource
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode

# from dodal.devices.pgm import PGM
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


# # Connect will work again after this work completed
# # https://jira.diamond.ac.uk/browse/I09-651
@device_factory()
def analyser_driver() -> VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]:
    energy_sources = {
        SelectedSource.SOURCE1: pgm().energy.user_readback,
        SelectedSource.SOURCE2: dcm().energy_in_ev,
    }
    return VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        pass_energy_type=PassEnergy,
        energy_sources=energy_sources,
    )
