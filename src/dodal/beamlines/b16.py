from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.epics.adcore import (
    ADBaseIO,
    ADTIFFWriter,
    AreaDetector,
)
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.common.visit import (
    RemoteDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.device_manager import DeviceManager
from dodal.devices.controllers import ConstantDeadTimeController
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b16")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/dls/b16/data/2025/cm40635-3/bluesky"),
        client=RemoteDirectoryServiceClient("http://b16-control:8088/api"),
    )


@devices.factory()
def attol1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT0")


@devices.factory()
def attol2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT1")


@devices.factory()
def attol3() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT2")


@devices.factory()
def attorot1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-02:ACT2")


@devices.factory()
def fds2(path_provider: PathProvider) -> AreaDetector:
    prefix = f"{PREFIX.beamline_prefix}-EA-FDS-02:"
    return AreaDetector(
        writer=ADTIFFWriter.with_io(prefix, path_provider, fileio_suffix=TIFF_SUFFIX),
        controller=ConstantDeadTimeController(
            driver=ADBaseIO(prefix + CAM_SUFFIX), deadtime=0.0
        ),
    )


@devices.factory()
def sim_stage() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-SIM-01:",
        x_infix="M1",
        y_infix="M2",
        z_infix="M3",
    )
