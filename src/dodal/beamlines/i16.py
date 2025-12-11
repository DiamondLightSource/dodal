from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.undulator import UndulatorInMm
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i16")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


@device_factory()
def id() -> UndulatorInMm:
    return UndulatorInMm(
        name="id", prefix=f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:"
    )
