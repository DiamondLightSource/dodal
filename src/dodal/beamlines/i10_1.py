from dodal.beamlines.i10_shared import devices as i10_shared_devices

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import I10JDiagnostic, I10JSlits, PiezoMirror
from dodal.devices.temperture_controller.lakeshore.lakeshore import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix("i10", "J")
devices = DeviceManager()
devices.include(i10_shared_devices)


@devices.factory()
def em_temperature_controller() -> Lakeshore336:
    return Lakeshore336(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-41:",
    )


@devices.factory()
def slits() -> I10JSlits:
    return I10JSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@devices.factory()
def diagnostic() -> I10JDiagnostic:
    return I10JDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@devices.factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCA-01:")
