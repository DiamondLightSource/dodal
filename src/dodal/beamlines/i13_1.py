from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.epics.adaravis import AravisDetector

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i13_1.merlin import Merlin
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i13-1")
PREFIX_BL13I = BeamlinePrefix(BL)  # Can't use this yet as returns BL13I
PREFIX = "BL13J"
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/dls/i13-1/data/2024/cm37257-5/tmp/"),  # latest commissioning visit
        client=LocalDirectoryServiceClient(),
    )


@devices.factory()
def sample_xyz_stage() -> XYZStage:
    return XYZStage(prefix=f"{PREFIX}-MO-PI-02:")


@devices.factory()
def sample_xyz_lab_fa_stage() -> XYZStage:
    return XYZStage(prefix=f"{PREFIX}-MO-PI-02:FIXANG:")


@devices.factory()
def side_camera(path_provider: PathProvider) -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX}-OP-FLOAT-03:",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=path_provider,
    )


@devices.factory()
def merlin(path_provider: PathProvider) -> Merlin:
    return Merlin(
        prefix=f"{PREFIX}-EA-DET-04:",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=path_provider,
    )
