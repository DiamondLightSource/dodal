from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

beamline = get_beamline_name("k11")
PREFIX = BeamlinePrefix(beamline)
set_log_beamline(beamline)
set_utils_beamline(beamline)

devices = DeviceManager()


@devices.factory()
def kb_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-KBM-01:CS:X")


@devices.factory()
def kb_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-KBM-01:CS:Y")
