from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.devices.i09.enums import Grating
from dodal.devices.pgm import PGM
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09")
PREFIX = BeamlinePrefix(BL, suffix="J")


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-MO-PGM-01:", grating=Grating)
