from pathlib import Path

from ophyd_async.core import AutoIncrementFilenameProvider, StaticPathProvider
from ophyd_async.epics.adandor import Andor2Detector, Andor2DriverIO
from ophyd_async.epics.adcore import SingleTriggerDetector
from ophyd_async.epics.core import epics_signal_r

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    set_beamline,
)
from dodal.devices.attenuator.filter import FilterMotor
from dodal.devices.attenuator.filter_selections import P99FilterSelections
from dodal.devices.motors import XYZPositioner
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


andor_data_path = StaticPathProvider(
    filename_provider=AutoIncrementFilenameProvider(base_filename="andor2"),
    directory_path=Path("/dls/p99/data/2024/cm37284-2/processing/writenData"),
)


@device_factory()
def andor2_det() -> Andor2Detector:
    """Andor model:DU897_BV."""
    return Andor2Detector(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-03:",
        path_provider=andor_data_path,
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
    )


@device_factory()
def andor2_point() -> SingleTriggerDetector:
    """Using the andor2 as if it is a massive point detector, read the meanValue after
    a picture is taken."""
    return SingleTriggerDetector(
        drv=Andor2DriverIO(f"{PREFIX.beamline_prefix}-EA-DET-03:CAM:"),
        read_uncached=[epics_signal_r(float, "BL10I-EA-PIMTE-01:STAT:MeanValue_RBV")],
    )
