from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.motors import (
    SixAxisGonioKappaGeometry,
    XYStage,
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
def armds() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:ARM:DS")


@device_factory()
def armus() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:ARM:US")


@device_factory()
def beamstop() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-RS-ABSB-04:")


@device_factory()
def bs2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-RS-ABSB-08:")


@device_factory()
def bs3() -> XYStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-RS-ABSB-09:")


@device_factory()
def dcmbragg1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL1:THETA")


@device_factory()
def dcmbragg2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL2:THETA")


@device_factory()
def dcmenergy() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:ENERGY")


@device_factory()
def dcmenergy_cal() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:CAL")


@device_factory()
def dcmx1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:X1")


@device_factory()
def dcmxtl1roll() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL1:ROLL")


@device_factory()
def dcmxtl1y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL1:Y")


@device_factory()
def dcmxtl1z() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL1:Z")


@device_factory()
def dcmxtl2y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-DCM-01:XTAL2:Y")


@device_factory()
def det1z() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:ARM:DETECTOR:Z")


@device_factory()
def det2z() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:DETECTOR2:Z")


@device_factory()
def diffractometer() -> SixAxisGonioKappaGeometry:
    return SixAxisGonioKappaGeometry(
        prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:SAMPLE:",
        theta_infix="KTHETA",
        phi_infix="KPHI",
    )


@device_factory()
def djack1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:Y1")


@device_factory()
def djack2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:Y2")


@device_factory()
def djack3() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:Y3")


@device_factory()
def drotation() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:Ry")


@device_factory()
def dtransx() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:X")


@device_factory()
def eht2dtx() -> Motor:
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
def hfm_curve() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:CURVE")


@device_factory()
def hfm_ellipticity() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:ELLIP")


@device_factory()
def hfm_pitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:PITCH")


@device_factory()
def hfm_roll() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:ROLL")


@device_factory()
def hfm_yaw() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:YAW")


@device_factory()
def hfm_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:X")


@device_factory()
def hfm_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-HFM-01:Y")


@device_factory()
def laserboard() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:")


@device_factory()
def objds() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OBJ:DS")


@device_factory()
def objus() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OBJ:US")


@device_factory()
def opticxds() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:DS:X")


@device_factory()
def opticxus() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:US:X")


@device_factory()
def opticyds() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:DS:Y")


@device_factory()
def opticyus() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-LHEAT-01:OPTIC:US:Y")


@device_factory()
def pin3() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-AL-APTR-03:")


@device_factory()
def pinpitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-AL-APTR-02:PITCH")


@device_factory()
def pinx() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-AL-APTR-02:X")


@device_factory()
def piny() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-AL-APTR-02:Y")


@device_factory()
def pinyaw() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-AL-APTR-02:YAW")


@device_factory()
def pinz() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-AL-APTR-02:Z")


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
def shfmcurve() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:HFM:CURVE")


@device_factory()
def shfmellip() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:HFM:ELLIP")


@device_factory()
def shfmpitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:HFM:PITCH")


@device_factory()
def shfmx() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:HFM:X")


@device_factory()
def skbjack1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:J1")


@device_factory()
def skbjack2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:J2")


@device_factory()
def skbjack3() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:J3")


@device_factory()
def skbpitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:PITCH")


@device_factory()
def skbroll() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:ROLL")


@device_factory()
def skby() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:BASE:Y")


@device_factory()
def svfmcurve() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:VFM:CURVE")


@device_factory()
def svfmellip() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:VFM:ELLIP")


@device_factory()
def svfmpitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:VFM:PITCH")


@device_factory()
def svfmy() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-03:VFM:Y")


@device_factory()
def tab2jack1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:Y1")


@device_factory()
def tab2jack2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:Y2")


@device_factory()
def tab2jack3() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:Y3")


@device_factory()
def tab2rotation() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:Ry")


@device_factory()
def tab2transx() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-03:BASE:X")


@device_factory()
def vfm_curve() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:CURVE")


@device_factory()
def vfm_ellipticity() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:ELLIP")


@device_factory()
def vfm_pitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:PITCH")


@device_factory()
def vfm_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:X")


@device_factory()
def vfm_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:Y")


@device_factory()
def vfm_yaw() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-VFM-01:YAW")


@device_factory(skip=BL == "i15")
def synchrotron() -> Synchrotron:
    return Synchrotron()
