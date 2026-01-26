from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import (
    I10SharedSlits,
)

# Imports taken from i10 while we work out how to deal with split end stations
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_shared_slit = DeviceManager()
"""Slits"""


@devices_shared_slit.factory()
def optics_slits() -> I10SharedSlits:
    return I10SharedSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")
