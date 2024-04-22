from functools import lru_cache

from ophyd_async.core import DirectoryProvider

from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.areadetector import AdAravisDetector
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("p38")
set_log_beamline(BL)
set_utils_beamline(BL)


@lru_cache
def get_directory_provider() -> DirectoryProvider:
    return StaticVisitDirectoryProvider(
        BL,
        "/data/2024/cm37282-2/",  # latest commissioning visit
    )


def d11(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "D11",
        "-DI-DCAM-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d12(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> AdAravisDetector:
    return device_instantiation(
        AdAravisDetector,
        "D12",
        "-DI-DCAM-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-01",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
