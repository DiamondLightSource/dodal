from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.motors import EpicsMotor
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, get_hostname, skip_device

BL = get_beamline_name("i20-1")
set_log_beamline(BL)
set_utils_beamline(BL)


def _is_i20_1_machine():
    """
    Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i20-1")


@skip_device(lambda: not _is_i20_1_machine())
def turbo_slit_motor() -> EpicsMotor:
    """Get the i20-1 motor"""

    return device_instantiation(
        EpicsMotor,
        "BL20J-OP-PCHRO-01:TS:XFINE",
        "turbo_slit_motor_x",
        wait=False,
        fake=False,
    )
