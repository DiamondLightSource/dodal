from functools import lru_cache

from ophyd_async.core import DirectoryProvider

from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i22")
set_log_beamline(BL)
set_utils_beamline(BL)


@lru_cache
def get_directory_provider() -> DirectoryProvider:
    """VISIT is a placeholder value for reference.
    Requires that all StandardDetector IOCs are running with /data mapping to /dls/i22/data
    """
    return StaticVisitDirectoryProvider(
        BL,
        "/data/i22/2024/VISIT",
    )


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-02",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def it(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "it",
        "-EA-TTRM-02",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
