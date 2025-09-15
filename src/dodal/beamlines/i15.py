from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i15.dcm import DCM
from dodal.devices.i15.focussing_mirror import (
    FocusingMirror,
    FocusingMirrorHorizontal,
    FocusingMirrorVertical,
    FocusingMirrorWithRoll,
)
from dodal.devices.i15.jack import JackX, JackY
from dodal.devices.i15.motors import UpstreamDownstreamPair
from dodal.devices.motors import (
    SixAxisGonioKappaPhi,
    XYStage,
    XYZPitchYawStage,
    XYZStage,
)
from dodal.devices.slits import Slits, SlitsY
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i15")  # Default used when not on a live beamline
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)  # Configure logging and util functions
set_utils_beamline(BL)

"""
Define device factory functions below this point.
A device factory function is any function that has a return type which conforms
to one or more Bluesky Protocols.
"""


@device_factory()
def arm() -> UpstreamDownstreamPair:
    return UpstreamDownstreamPair(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:ARM:")


@device_factory()
def beamstop() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-RS-ABSB-04:")


@device_factory()
def bs2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-RS-ABSB-08:")


@device_factory()
def bs3() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-RS-ABSB-09:")


@device_factory()
def dcm() -> DCM:
    return DCM(f"{PREFIX.beamline_prefix}-OP-DCM-01:")


@device_factory()
def det1z() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:ARM:DETECTOR:Z")


@device_factory()
def det2z() -> Motor:
    """Deliberately the same as eht2dtx"""
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:DETECTOR2:Z")


@device_factory()
def diffractometer() -> SixAxisGonioKappaPhi:
    return SixAxisGonioKappaPhi(
        prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:SAMPLE:",
        phi_infix="KPHI",
    )


@device_factory()
def djack1() -> JackX:
    return JackX(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:")


@device_factory()
def eht2dtx() -> Motor:
    """Deliberately the same as det2z"""
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:DETECTOR2:Z")


@device_factory()
def f2x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-RS-ABSB-10:X")


@device_factory()
def fs() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-EA-SHTR-01:")


@device_factory()
def fs2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-EA-SHTR-02:")


@device_factory()
def hfm() -> FocusingMirrorWithRoll:
    return FocusingMirrorWithRoll(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@device_factory()
def laserboard() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:")


@device_factory()
def obj() -> UpstreamDownstreamPair:
    return UpstreamDownstreamPair(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OBJ:")


@device_factory()
def opticds() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:DS:")


@device_factory()
def opticus() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:US:")


@device_factory()
def pin3() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-AL-APTR-03:")


@device_factory()
def pin() -> XYZPitchYawStage:
    return XYZPitchYawStage(f"{PREFIX.beamline_prefix}-AL-APTR-02:")


@device_factory()
def qbpm1() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-DI-QBPM-01:")


@device_factory()
def qbpm2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-DI-QBPM-02:")


@device_factory()
def s1() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def s2() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def s4() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def s5() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def s6() -> SlitsY:
    return SlitsY(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:",
        y_centre="Y:CENTER",
    )


@device_factory()
def s7() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-07:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def shd() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-SHEAD-01:")


@device_factory()
def shd2() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-SHEAD-02:")


@device_factory()
def shfm() -> FocusingMirrorHorizontal:
    return FocusingMirrorHorizontal(f"{PREFIX.beamline_prefix}-OP-MIRR-03:HFM:")


@device_factory()
def skb() -> JackY:
    return JackY(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:")


@device_factory()
def svfm() -> FocusingMirrorVertical:
    return FocusingMirrorVertical(f"{PREFIX.beamline_prefix}-OP-MIRR-03:VFM:")


@device_factory()
def tab2jack() -> JackX:
    return JackX(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:")


@device_factory()
def vfm() -> FocusingMirror:
    return FocusingMirror(f"{PREFIX.beamline_prefix}-OP-VFM-01:")


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
