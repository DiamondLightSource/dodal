from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i23.gonio import Gonio
from dodal.devices.oav.edge_detection.oav_with_edge_detection import EdgeDetection
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i23")
set_log_beamline(BL)
set_utils_beamline(BL)


def gonio(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Gonio:
    """Get the i23 goniometer device"""
    return device_instantiation(
        Gonio,
        "Gonio",
        "-MO-GONIO-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def oav_pin_tip_detection(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> EdgeDetection:
    """Get the i23 OAV pin-tip detection device"""
    return device_instantiation(
        EdgeDetection,
        "PinTipDetection",
        "BL03I-DI-OAV-01:",  # TODO: FIXME
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )
