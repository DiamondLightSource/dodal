from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, get_hostname

BL = get_beamline_name("i23")
set_log_beamline(BL)
set_utils_beamline(BL)

PREFIX = BeamlinePrefix(BL)


def _is_i23_machine():
    """
    Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i23-ws") or hostname.startswith("i23-control")


@device_factory(skip=lambda: not _is_i23_machine())
def oav_pin_tip_detection() -> PinTipDetection:
    """Get the i23 OAV pin-tip detection device"""

    return PinTipDetection(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        "pin_tip_detection",
    )
