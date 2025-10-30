from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.i09_1 import LensMode, PsuMode
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import UndulatorOrder
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
def dcm() -> DoubleCrystalMonochromatorWithDSpacing:
    return DoubleCrystalMonochromatorWithDSpacing(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:", PitchAndRollCrystal, StationaryCrystal
    )


@device_factory()
def energy_source() -> EnergySource:
    return EnergySource(dcm().energy_in_eV)


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/I09-651
@device_factory()
def analyser() -> SpecsDetector[LensMode, PsuMode]:
    return SpecsDetector[LensMode, PsuMode](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-02:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        energy_source=energy_source(),
    )


@device_factory()
def harmonics() -> UndulatorOrder:
    return UndulatorOrder(name="harmonics")
