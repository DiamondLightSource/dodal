from dodal.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.slits import Slits
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

from ._device_helpers import numbered_slits
from .beamline_utils import device_instantiation, get_directory_provider
from .beamline_utils import set_beamline as set_utils_beamline

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


def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        1,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        2,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        3,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        4,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_5(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        5,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_6(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        6,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def fswitch(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FSwitch:
    return device_instantiation(
        FSwitch,
        "fswitch",
        "-MO-FSWT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
