from dodal.beamlines.beamline_utils import device_instantiation
from dodal.devices.i23.gonio import Gonio
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline


BL = get_beamline_name("i23")
set_log_beamline(BL)
set_utils_beamline(BL)


def gonio(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Gonio:
    """Get the i23 goniometer device
    """
    return device_instantiation(
        Gonio,
        "Gonio",
        "-MO-GONIO-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
