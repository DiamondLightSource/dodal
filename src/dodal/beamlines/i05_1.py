from dodal.beamline_specific_utils.i05_shared import m1 as i05_m1
from dodal.beamline_specific_utils.i05_shared import m3mj6 as i05_m3mj6
from dodal.beamline_specific_utils.i05_shared import pgm as i05_pgm
from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_mirror import XYZCollMirror, XYZPiezoCollMirror
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def pgm() -> PGM:
    return i05_pgm()


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# BL05 shared devices


@device_factory()
def pgm() -> PGM:
    return i05_pgm()


@device_factory()
def m1() -> XYZCollMirror:
    return i05_m1()


@device_factory()
def m3mj6() -> XYZPiezoCollMirror:
    return i05_m3mj6()


# beamline specific devices


@device_factory()
def mj7j8() -> XYZPiezoCollMirror:
    return XYZPiezoCollMirror(prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:")
