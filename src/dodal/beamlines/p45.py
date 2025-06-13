from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import StaticVisitPathProvider
from dodal.devices.p45 import Choppers, TomoStageWithStretchAndSkew
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p45")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/data/2024/cm37283-2/"),  # latest commissioning visit
    )
)


@device_factory()
def sample() -> TomoStageWithStretchAndSkew:
    return TomoStageWithStretchAndSkew(f"{PREFIX.beamline_prefix}-MO-STAGE-01:")


@device_factory()
def choppers() -> Choppers:
    return Choppers(f"{PREFIX.beamline_prefix}-MO-CHOP-01:")


# Disconnected
@device_factory(skip=True)
def det() -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-EA-MAP-01:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


# Disconnected
@device_factory(skip=True)
def diff() -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-EA-DIFF-01:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@device_factory(skip=True)
def panda1() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda2() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-02:",
        path_provider=get_path_provider(),
    )
