from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i05.enums import Mj7j8Mirror
from dodal.devices.common_mirror import XYZPiezoSwitchingMirror
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i05_shared_devices)


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@devices.factory(skip=True)
def mj7j8() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=Mj7j8Mirror,
    )
