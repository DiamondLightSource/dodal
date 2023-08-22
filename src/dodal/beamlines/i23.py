from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i23.gonio import Gonio
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, get_hostname, skip_device

BL = get_beamline_name("i23")
set_log_beamline(BL)
set_utils_beamline(BL)


def _is_i23_machine():
    """
    Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i23-ws") or hostname.startswith("i23-control")


def gonio(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Gonio:
    """Get the i23 goniometer device"""
    return device_instantiation(
        Gonio,
        "Gonio",
        "-MO-GONIO-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: not _is_i23_machine())
def oav_pin_tip_detection(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PinTipDetection:
    """Get the i23 OAV pin-tip detection device"""

    return device_instantiation(
        PinTipDetection,
        "pin_tip_detection",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
