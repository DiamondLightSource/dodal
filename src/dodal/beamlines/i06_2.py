from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_2 import PEEMManipulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06_2")
PREFIX = BeamlinePrefix(BL, suffix="K")
set_log_beamline(BL)
set_utils_beamline(BL)


devices = DeviceManager()


@devices.factory
def peem() -> PEEMManipulator:
    return PEEMManipulator(f"{PREFIX.beamline_prefix}-MO-PEEM-01:")
