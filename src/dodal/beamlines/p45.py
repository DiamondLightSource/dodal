from ophyd_async.epics.areadetector import AravisDetector
from ophyd_async.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.p45 import Choppers, TomoStageWithStretchAndSkew
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

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


# Disconnected
@skip_device
def det(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "det",
        "-EA-MAP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
    )


# Disconnected
@skip_device
def diff(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "diff",
        "-EA-DIFF-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
    )


# Must find which PandA IOC(s) are compatible
# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@skip_device
def panda1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda1",
        "-MO-PANDA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


@skip_device
def panda2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda2",
        "-MO-PANDA-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
