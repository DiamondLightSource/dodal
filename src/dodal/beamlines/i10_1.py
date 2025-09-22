from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i10 import I10JDiagnostic, I10JSlits
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix("i10", "J")


@device_factory()
def slits() -> I10JSlits:
    return I10JSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@device_factory()
def diagnostic() -> I10JDiagnostic:
    return I10JDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )
