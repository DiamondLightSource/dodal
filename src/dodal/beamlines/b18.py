from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.device_manager import DeviceManager
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b18")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/dls/b18/data/2025/cm40637-3/bluesky"),
        client=LocalDirectoryServiceClient(),
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
