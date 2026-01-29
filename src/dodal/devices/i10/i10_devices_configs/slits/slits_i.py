from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import (
    I10Slits,
    I10SlitsDrainCurrent,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_slit_i = DeviceManager()


@devices_slit_i.factory()
def slits() -> I10Slits:
    return I10Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@devices_slit_i.factory()
def slits_current() -> I10SlitsDrainCurrent:
    return I10SlitsDrainCurrent(prefix=f"{PREFIX.beamline_prefix}-")
