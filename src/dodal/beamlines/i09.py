from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser import DualEnergySource
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.i09 import Grating, LensMode, PassEnergy, PsuMode
from dodal.devices.pgm import PlaneGratingMonochromator
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
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{BeamlinePrefix(BL, suffix='J').beamline_prefix}-MO-PGM-01:",
        grating=Grating,
    )


@device_factory()
def dcm() -> DoubleCrystalMonochromatorWithDSpacing:
    return DoubleCrystalMonochromatorWithDSpacing(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:", PitchAndRollCrystal, StationaryCrystal
    )


@device_factory()
def energy_source() -> DualEnergySource:
    return DualEnergySource(dcm().energy_in_eV, pgm().energy.user_readback)


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/I09-651
@device_factory()
def ew4000() -> VGScientaDetector[LensMode, PsuMode, PassEnergy]:
    return VGScientaDetector[LensMode, PsuMode, PassEnergy](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        pass_energy_type=PassEnergy,
        energy_source=energy_source(),
    )
