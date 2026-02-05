from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i05.enums import M4M5Mirror
from dodal.devices.common_mirror import XYZSwitchingMirror
from dodal.devices.temperture_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

devices = DeviceManager()
devices.include(i05_shared_devices)

BL = get_beamline_name("i05")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@devices.factory(skip=True)
def m4m5() -> XYZSwitchingMirror:
    return XYZSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=M4M5Mirror,
    )


@devices.factory()
def sample_temperature_controller() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-02:")
