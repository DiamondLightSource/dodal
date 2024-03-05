from ophyd_async.panda import PandA

from dodal.beamlines.beamline_utils import device_instantiation, get_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i22.pilatus import I22HDFStatsPilatus
from dodal.devices.linkam3 import Linkam3
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i22")
set_log_beamline(BL)
set_utils_beamline(BL)


def saxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I22HDFStatsPilatus:
    return device_instantiation(
        I22HDFStatsPilatus,
        "saxs",
        "-EA-PILAT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def waxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I22HDFStatsPilatus:
    return device_instantiation(
        I22HDFStatsPilatus,
        "waxs",
        "-EA-PILAT-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def panda(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> PandA:
    return device_instantiation(
        PandA, "panda-01", "-EA-PANDA-01:", wait_for_connection, fake_with_ophyd_sim
    )


def linkam(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Linkam3:
    return device_instantiation(
        Linkam3, "linkam", "-EA-TEMPC-05", wait_for_connection, fake_with_ophyd_sim
    )


def tetramm1(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
        temperature="Temperature",
    )


def tetramm2(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "it",
        "-EA-TTRM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
