from pathlib import Path

from ophyd_async.epics.adandor import Andor2Detector

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_beamline,
    set_path_provider,
)
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.attenuator.filter import FilterMotor
from dodal.devices.attenuator.filter_selections import P99FilterSelections
from dodal.devices.motors import XYZPositioner
from dodal.devices.p99.andor2_point import Andor2Point
from dodal.devices.p99.sample_stage import SampleAngleStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p99")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_beamline(BL)


@device_factory()
def angle_stage() -> SampleAngleStage:
    return SampleAngleStage(f"{PREFIX.beamline_prefix}-MO-STAGE-01:")


@device_factory()
def filter() -> FilterMotor:
    return FilterMotor(f"{PREFIX.beamline_prefix}-MO-STAGE-02:MP:", P99FilterSelections)


@device_factory()
def sample_stage() -> XYZPositioner:
    return XYZPositioner(f"{PREFIX.beamline_prefix}-MO-STAGE-02:")


@device_factory()
def lab_stage() -> XYZPositioner:
    return XYZPositioner(f"{PREFIX.beamline_prefix}-MO-STAGE-02:LAB:")


set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/p99/data/2024/cm37284-2/processing/writenData"),
        client=LocalDirectoryServiceClient(),  # RemoteDirectoryServiceClient("http://p99-control:8088/api"),
    )
)


@device_factory()
def andor2_det() -> Andor2Detector:
    """Andor model:DU897_BV."""
    return Andor2Detector(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-03:",
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@device_factory()
def andor2_point() -> Andor2Point:
    """Using the andor2 as if it is a massive point detector, read the meanValue and total after
    a picture is taken."""
    return Andor2Point(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-03:",
        drv_suffix=CAM_SUFFIX,
        read_uncached={"mean": "STAT:MeanValue_RBV", "total": "STAT:Total_RBV"},
    )
