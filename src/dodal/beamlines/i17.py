"""The I17 hardware doesn't exist yet, but this configuration file is useful for
creating plans in sm-bluesky as devices build up."""

from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i17")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


class I17Grating(StrictEnum):
    AU_400 = "400 line/mm Au"
    SI_400 = "400 line/mm Si"


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory(skip=True)
def pgm() -> PGM:
    return PGM(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I17Grating,
        gratingPv="NLINES2",
    )
