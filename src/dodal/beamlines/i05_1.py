from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

devices = DeviceManager()
devices.combine(i05_shared_devices)

BL = get_beamline_name("i05-1")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@devices.factory()
def sm() -> XYZStage:
    return XYZStage(
        f"{J_PREFIX.beamline_prefix}-EA-SM-01:",
        x_infix="SMX",
        y_infix="SMY",
        z_infix="SMZ",
    )
