from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.areadetector import AdAravisDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("p38")
set_log_beamline(BL)
set_utils_beamline(BL)


def d11(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "D11",
        "-DI-DCAM-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d12(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "D12",
        "-DI-DCAM-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
