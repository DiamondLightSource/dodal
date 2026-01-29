from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import (
    PiezoMirror,
)
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_shared_mirror = DeviceManager()


@devices_shared_mirror.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices_shared_mirror.factory()
def first_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@devices_shared_mirror.factory()
def switching_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")
