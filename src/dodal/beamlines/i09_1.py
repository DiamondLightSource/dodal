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
from dodal.devices.i09_1_shared.energy import HardEnergy, HardInsertionDeviceEnergy
from dodal.devices.i09_1_shared.hard_undulator_functions import (
    calculate_gap_i09_hu,
)
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder
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
@device_factory(skip=True)
def analyser() -> SpecsDetector[LensMode, PsuMode]:
    return SpecsDetector[LensMode, PsuMode](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-02:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        energy_source=energy_source(),
    )


@device_factory()
def undulator() -> UndulatorInMm:
    return UndulatorInMm(prefix=f"{PREFIX.beamline_prefix}-MO-UND-01:")


@device_factory()
def harmonics() -> UndulatorOrder:
    return UndulatorOrder(name="harmonics")


@device_factory()
def hu_id_energy() -> HardInsertionDeviceEnergy:
    return HardInsertionDeviceEnergy(
        undulator_order=harmonics(),
        undulator=undulator(),
        lut={},  # Placeholder, will be set later_
        gap_to_energy_func=lambda x: x,  # Placeholder, need https://github.com/DiamondLightSource/dodal/pull/1712 merged first
        energy_to_gap_func=calculate_gap_i09_hu,
        name="hu_id_energy",
    )


@device_factory()
def hu_energy() -> HardEnergy:
    return HardEnergy(
        dcm=dcm(),
        undulator_energy=hu_id_energy(),
        name="hu_energy",
    )
