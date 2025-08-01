from dodal.beamline_specific_utils.i05_shared import (
    m1_collimating_mirror,
    m3mj6_switching_mirror,
)
from dodal.beamline_specific_utils.i05_shared import pgm as i05_pgm
from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.common_mirror import XYZPiezoSwitchingMirror, XYZSwitchingMirror
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# BL05 shared devices


@device_factory()
def pgm() -> PGM:
    return i05_pgm()


@device_factory()
def m1() -> XYZPitchYawRollStage:
    return m1_collimating_mirror()


@device_factory()
def m3mj6() -> XYZPiezoSwitchingMirror:
    return m3mj6_switching_mirror()


# beamline specific devices


@device_factory()
def m4m5() -> XYZSwitchingMirror:
    return XYZSwitchingMirror(prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:")
