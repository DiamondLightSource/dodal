from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.i13_1.merlin import Merlin
from dodal.devices.motors import XYZPositioner
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i13-1")
PREFIX_BL13I = BeamlinePrefix(BL)  # Can't use this yet as returns BL13I
PREFIX = "BL13J"
set_log_beamline(BL)
set_utils_beamline(BL)
set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/i13-1/data/2024/cm37257-5/tmp/"),  # latest commissioning visit
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def sample_xyz_stage() -> XYZPositioner:
    return XYZPositioner(prefix=f"{PREFIX}-MO-PI-02:")


@device_factory()
def sample_xyz_lab_fa_stage() -> XYZPositioner:
    return XYZPositioner(prefix=f"{PREFIX}-MO-PI-02:FIXANG:")


@device_factory()
def side_camera() -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX}-OP-FLOAT-03:",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=get_path_provider(),
    )


@device_factory()
def merlin() -> Merlin:
    return Merlin(
        prefix=f"{PREFIX}-EA-DET-04:",
        name="merlin",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=get_path_provider(),
    )
