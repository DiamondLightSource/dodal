from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.common_mirror import XYZCollimatingMirror, XYZPiezoCollimatingMirror
from dodal.devices.i05.enums import Grating
from dodal.devices.pgm import PGM
from dodal.utils import BeamlinePrefix

PREFIX = BeamlinePrefix("i05", "I")


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=Grating)


@device_factory()
def m1() -> XYZCollimatingMirror:
    return XYZCollimatingMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def m3mj6() -> XYZPiezoCollimatingMirror:
    return XYZPiezoCollimatingMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")
