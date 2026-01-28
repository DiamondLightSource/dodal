from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i05_1.motors import XYZPolarAzimuthDefocusStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i05_shared_devices)


@devices.factory
def sm() -> XYZPolarAzimuthDefocusStage:
    "Sample manipulator"
    return XYZPolarAzimuthDefocusStage(prefix=f"{PREFIX.beamline_prefix}-EA-SM-01:")
