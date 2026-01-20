from dodal.beamlines.i05_shared import devices as i05_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i05_devices)
