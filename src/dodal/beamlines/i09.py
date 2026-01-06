from ophyd_async.core import InOut

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser.base import (
    DualEnergySource,
)
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.i09 import Grating, LensMode, PassEnergy, PsuMode
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import SourceSelector
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller import (
    Lakeshore336,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09")
I_PREFIX = BeamlinePrefix(BL, suffix="I")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def source_selector() -> SourceSelector:
    return SourceSelector()


@device_factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{J_PREFIX.beamline_prefix}-MO-PGM-01:", grating=Grating
    )


@device_factory()
def dcm() -> DoubleCrystalMonochromatorWithDSpacing:
    return DoubleCrystalMonochromatorWithDSpacing(
        f"{I_PREFIX.beamline_prefix}-MO-DCM-01:", PitchAndRollCrystal, StationaryCrystal
    )


@device_factory()
def dual_energy_source() -> DualEnergySource:
    return DualEnergySource(
        dcm().energy_in_eV,
        pgm().energy.user_readback,
        source_selector().selected_source,
    )


@device_factory()
def fsi1() -> GenericFastShutter[InOut]:
    return GenericFastShutter[InOut](
        f"{I_PREFIX.beamline_prefix}-EA-FSHTR-01:CTRL", InOut.OUT, InOut.IN
    )


@device_factory()
def fsj1() -> GenericFastShutter[InOut]:
    return GenericFastShutter[InOut](
        f"{J_PREFIX.beamline_prefix}-EA-FSHTR-01:CTRL", InOut.OUT, InOut.IN
    )


@device_factory()
def dual_fast_shutter() -> DualFastShutter[InOut]:
    return DualFastShutter[InOut](fsi1(), fsj1(), source_selector().selected_source)


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/I09-651
@device_factory()
def ew4000() -> VGScientaDetector[LensMode, PsuMode, PassEnergy]:
    return VGScientaDetector[LensMode, PsuMode, PassEnergy](
        prefix=f"{I_PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        pass_energy_type=PassEnergy,
        energy_source=dual_energy_source(),
        shutter=dual_fast_shutter(),
        source_selector=source_selector(),
    )


@device_factory()
def lakeshore() -> Lakeshore336:
    return Lakeshore336(prefix="BL09L-VA-LAKE-01:")
