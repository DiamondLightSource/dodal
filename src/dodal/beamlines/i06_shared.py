from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.devices.i06_shared import Grating
from dodal.devices.pgm import PGM
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06")
PREFIX = BeamlinePrefix(BL, suffix="I")


@device_factory()
def pgm() -> PGM:
    return PGM(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
        gratingPv="NLINES2",
    )
