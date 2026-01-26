from dodal.beamlines.i09_2_shared import devices as i09_2_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-2")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i09_2_shared_devices)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
