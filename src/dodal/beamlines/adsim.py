from dodal.beamlines.beamline_utils import device_instantiation, get_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.adsim import SimStage
from dodal.devices.areadetector import AdSimDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, get_hostname

BL = get_beamline_name(get_hostname())
set_log_beamline(BL)
set_utils_beamline(BL)


def stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SimStage:
    return device_instantiation(
        SimStage,
        "sim_motors",
        "-MO-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def adsim(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AdSimDetector:
    return device_instantiation(
        AdSimDetector,
        "adsim",
        "-AD-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
