from dodal.common.beamlines.beamline_utils import device_factory, set_beamline
from dodal.devices.attenuator.filter import FilterMotor
from dodal.devices.attenuator.filter_selections import p99StageSelections
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
    return FilterMotor(
        p99StageSelections, f"{PREFIX.beamline_prefix}-MO-STAGE-02:MP:SELECT"
    )


@device_factory()
def sample_stage() -> XYZPositioner:
    return XYZPositioner(f"{PREFIX.beamline_prefix}-MO-STAGE-02:")


@device_factory()
def lab_stage() -> XYZPositioner:
    return XYZPositioner(f"{PREFIX.beamline_prefix}-MO-STAGE-02:LAB:")
