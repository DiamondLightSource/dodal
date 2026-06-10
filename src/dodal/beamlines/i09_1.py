from ophyd_async.epics.adcore import ADAcquireLogic

from dodal.beamlines.i09_1_shared import devices as i09_1_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i09_1 import LensMode, PsuMode
from dodal.devices.common_dcm import DoubleCrystalMonochromatorWithDSpacing
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO, SpecsDetector
from dodal.devices.motors import XYZAzimuthTiltPolarStage
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-1")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i09_1_shared_devices)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def analyser(
    dcm: DoubleCrystalMonochromatorWithDSpacing,
) -> SpecsDetector[LensMode, PsuMode]:
    prefix = f"{PREFIX.beamline_prefix}-EA-DET-02:CAM:"
    driver = SpecsAnalyserDriverIO(prefix, LensMode, PsuMode)
    return SpecsDetector[LensMode, PsuMode](
        prefix,
        driver,
        acquire_logic=ADAcquireLogic(driver),
        trigger_logic=ElectronAnalayserTriggerLogic(driver),
        region_logic=RegionLogic(driver, dcm.energy_in_eV),
    )


@devices.factory()
def lakeshore() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-01:")


@devices.factory()
def hsmpm() -> XYZAzimuthTiltPolarStage:
    """Sample Manipulator."""
    return XYZAzimuthTiltPolarStage(prefix=f"{PREFIX.beamline_prefix}-MO-HSMPM-01:")
