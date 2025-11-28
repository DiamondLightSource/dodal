from dodal.beamlines.i05_shared import PREFIX, devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i05")
set_log_beamline(BL)
set_utils_beamline(BL)


@devices.factory()
def sm() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-EA-SM-01:",
        x_infix="SAX",
        y_infix="SAY",
        z_infix="SAZ",
    )
