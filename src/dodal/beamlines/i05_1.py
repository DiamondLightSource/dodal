from ophyd_async.sim import SimMotor

from dodal.beamlines.i05_shared import devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@devices.factory()
def sim_motor() -> SimMotor:
    return SimMotor()
