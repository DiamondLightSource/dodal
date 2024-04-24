from dodal.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i22")
set_log_beamline(BL)
set_utils_beamline(BL)
"""VISIT is a placeholder value for reference.
    Requires that all StandardDetector IOCs are running with /data mapping to /dls/i22/data
    """
set_directory_provider(
    StaticVisitDirectoryProvider(
        BL,
        "/data/i22/2024/VISIT",
    )
)


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-02:",
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
        "-EA-TTRM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def vfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "vfm",
        "-OP-KBM-01:VFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def hfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "hfm",
        "-OP-KBM-01:HFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
