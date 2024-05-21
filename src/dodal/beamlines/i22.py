from pathlib import Path

from ophyd_async.epics.areadetector import AravisDetector, PilatusDetector
from ophyd_async.panda import HDFPanda

from dodal.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitDirectoryProvider
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.slits import Slits
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

from ._device_helpers import numbered_slits
from .beamline_utils import device_instantiation, get_directory_provider
from .beamline_utils import set_beamline as set_utils_beamline

BL = get_beamline_name("i22")
set_log_beamline(BL)
set_utils_beamline(BL)

# Currently we must hard-code the visit, determining the visit at runtime requires
# infrastructure that is still WIP.
# Communication with GDA is also WIP so for now we determine an arbitrary scan number
# locally and write the commissioning directory. The scan number is not guaranteed to
# be unique and the data is at risk - this configuration is for testing only.
set_directory_provider(
    StaticVisitDirectoryProvider(
        BL,
        Path("/dls/i22/data/2024/cm37271-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)


def saxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PilatusDetector:
    return device_instantiation(
        PilatusDetector,
        "saxs",
        "-EA-PILAT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
    )


def waxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PilatusDetector:
    return device_instantiation(
        PilatusDetector,
        "waxs",
        "-EA-PILAT-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
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


def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        1,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        2,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        3,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device
def slits_4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        4,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_5(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        5,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_6(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
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
    )


@skip_device
def panda3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda3",
        "-MO-PANDA-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device
def panda4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda4",
        "-MO-PANDA-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def oav(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "oav",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
    )
