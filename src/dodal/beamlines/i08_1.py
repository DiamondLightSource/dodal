from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.epics.motor import Motor
from ophyd_async.epics.pmac import PmacIO
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i08-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
# PATH = "/dls/i08/data/2026/cm44148-5/tmp"
PATH = "/tmp/"
set_log_beamline(BL)
set_utils_beamline(BL)

from ophyd_async.core import (
    StaticPathProvider,
    UUIDFilenameProvider,
)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticPathProvider(UUIDFilenameProvider(), Path(PATH))


@devices.factory()
def scanning_fine_x() -> Motor:
    """Turbo slit x motor."""
    return Motor(f"{PREFIX.beamline_prefix}-EA-TABLE-01:XF")


@devices.factory()
def scanning_fine_y() -> Motor:
    """Turbo slit x motor."""
    return Motor(f"{PREFIX.beamline_prefix}-EA-TABLE-01:YF")


@devices.factory()
def scanning_pmac() -> PmacIO:
    """PMac controller using running fly scans with trajectory."""
    return PmacIO(
        prefix=f"{PREFIX.beamline_prefix}-MO-STEP-01:",
        raw_motors=[scanning_fine_x()],
        coord_nums=[2],
        name="pmac",
    )


@devices.factory()
def panda1(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
