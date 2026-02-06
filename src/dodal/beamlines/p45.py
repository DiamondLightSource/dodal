from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.p45 import TomoStageWithStretchAndSkew
from dodal.devices.motors import XYStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p45")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/data/2024/cm37283-2/"),  # latest commissioning visit
    )


@devices.factory()
def sample() -> TomoStageWithStretchAndSkew:
    return TomoStageWithStretchAndSkew(f"{PREFIX.beamline_prefix}-MO-STAGE-01:")


@devices.factory()
def choppers() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-CHOP-01:")


# Disconnected
@devices.factory(skip=True)
def det(path_provider: PathProvider) -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-EA-MAP-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


# Disconnected
@devices.factory(skip=True)
def diff(path_provider: PathProvider) -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-EA-DIFF-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@devices.factory(skip=True)
def panda1(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory(skip=True)
def panda2(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-02:",
        path_provider=path_provider,
    )
