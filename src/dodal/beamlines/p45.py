from dodal.beamlines.beamline_utils import device_instantiation, set_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.areadetector import AdAravisDetector
from dodal.devices.p45 import Choppers, TomoStageWithStretchAndSkew
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("p45")
set_log_beamline(BL)
set_utils_beamline(BL)
set_directory_provider(
    StaticVisitDirectoryProvider(
        BL,
        "/data/2024/cm37283-2/",  # latest commissioning visit
    )
)


def sample(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TomoStageWithStretchAndSkew:
    return device_instantiation(
        TomoStageWithStretchAndSkew,
        "sample_stage",
        "-MO-STAGE-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def choppers(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Choppers:
    return device_instantiation(
        Choppers,
        "chopper",
        "-MO-CHOP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def det(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "det",
        "-EA-MAP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def diff(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "diff",
        "-EA-DIFF-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
