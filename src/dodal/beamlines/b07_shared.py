from dodal.device_manager import DeviceManager
from dodal.devices.synchrotron import Synchrotron
from dodal.utils import get_beamline_name

BL = get_beamline_name("b07-shared")

devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
