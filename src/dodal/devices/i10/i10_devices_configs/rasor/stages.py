from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10.rasor.rasor_motors import (
    DetSlits,
    Diffractometer,
    PaStage,
)
from dodal.devices.motors import XYStage, XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_pin_hole = DeviceManager()
devices_det_slits = DeviceManager()
devices_diffractometer = DeviceManager()
devices_pa_stage = DeviceManager()
devices_sample_stage = DeviceManager()


@devices_pin_hole.factory()
def pin_hole() -> XYStage:
    return XYStage(prefix="ME01D-EA-PINH-01:")


@devices_det_slits.factory()
def det_slits() -> DetSlits:
    return DetSlits(prefix="ME01D-MO-APTR-0")


@devices_diffractometer.factory()
def diffractometer() -> Diffractometer:
    return Diffractometer(prefix="ME01D-MO-DIFF-01:")


@devices_pa_stage.factory()
def pa_stage() -> PaStage:
    return PaStage(prefix="ME01D-MO-POLAN-01:")


@devices_sample_stage.factory()
def sample_stage() -> XYZStage:
    return XYZStage(prefix="ME01D-MO-CRYO-01:")
