from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_mirror import XYZCollMirror, XYZPiezoCollMirror
from dodal.devices.i05.enums import Grating
from dodal.devices.pgm import PGM
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-shared")
PREFIX = BeamlinePrefix("i05", "I")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=Grating)


@device_factory()
def m1() -> XYZCollMirror:
    return XYZCollMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def m3mj6() -> XYZPiezoCollMirror:
    return XYZPiezoCollMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")
