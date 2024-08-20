from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("10")
set_log_beamline(BL)
set_utils_beamline(BL)
