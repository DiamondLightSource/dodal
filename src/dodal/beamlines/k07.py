from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("k07")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# Grating does not exist yet - this class is a placeholder for when it does
class Grating(StrictEnum):
    NO_GRATING = "No Grating"


# Grating does not exist yet - this class is a placeholder for when it does
@device_factory(skip=True)
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=Grating)
