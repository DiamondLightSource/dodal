from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.baton import Baton
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i03")
set_log_beamline(BL)
set_utils_beamline(BL)

PREFIX = BeamlinePrefix(BL)


devices = DeviceManager()


@devices.factory()
def baton() -> Baton:
    return Baton(f"{PREFIX.beamline_prefix}-CS-BATON-01:")
