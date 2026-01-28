from ophyd_async.core import InOut

from dodal.beamlines.i09_1_shared import devices as i09_1_shared_devices
from dodal.beamlines.i09_2_shared import devices as i09_2_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.common_dcm import DoubleCrystalMonochromatorWithDSpacing
from dodal.devices.electron_analyser.base import DualEnergySource
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from dodal.devices.motors import XYZPolarAzimuthStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import SourceSelector
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09")
I_PREFIX = BeamlinePrefix(BL, suffix="I")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i09_1_shared_devices)
devices.include(i09_2_shared_devices)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def source_selector() -> SourceSelector:
    return SourceSelector()


@devices.factory()
def dual_energy_source(
    dcm: DoubleCrystalMonochromatorWithDSpacing,
    pgm: PlaneGratingMonochromator,
    source_selector: SourceSelector,
) -> DualEnergySource:
    return DualEnergySource(
        dcm.energy_in_eV,
        pgm.energy.user_readback,
        source_selector.selected_source,
    )


@devices.factory()
def fsi1() -> GenericFastShutter[InOut]:
    return GenericFastShutter[InOut](
        f"{I_PREFIX.beamline_prefix}-EA-FSHTR-01:CTRL",
        open_state=InOut.OUT,
        close_state=InOut.IN,
    )


@devices.factory()
def fsj1() -> GenericFastShutter[InOut]:
    return GenericFastShutter[InOut](
        f"{J_PREFIX.beamline_prefix}-EA-FSHTR-01:CTRL",
        open_state=InOut.OUT,
        close_state=InOut.IN,
    )


@devices.factory()
def dual_fast_shutter(
    fsi1: GenericFastShutter, fsj1: GenericFastShutter, source_selector: SourceSelector
) -> DualFastShutter[InOut]:
    return DualFastShutter[InOut](fsi1, fsj1, source_selector.selected_source)


# CAM:IMAGE will fail to connect outside the beamline network,
# see https://github.com/DiamondLightSource/dodal/issues/1852
@devices.factory()
def ew4000(
    dual_fast_shutter: DualFastShutter,
    dual_energy_source: DualEnergySource,
    source_selector: SourceSelector,
) -> VGScientaDetector[LensMode, PsuMode, PassEnergy]:
    return VGScientaDetector[LensMode, PsuMode, PassEnergy](
        prefix=f"{I_PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        pass_energy_type=PassEnergy,
        energy_source=dual_energy_source,
        shutter=dual_fast_shutter,
        source_selector=source_selector,
    )


@devices.factory()
def lakeshore() -> Lakeshore336:
    return Lakeshore336(prefix="BL09L-VA-LAKE-01:")


@devices.factory()
def smpm() -> XYZPolarAzimuthStage:
    """Sample Manipulator"""
    return XYZPolarAzimuthStage(prefix=f"{I_PREFIX.beamline_prefix}-MO-SMPM-01:")
