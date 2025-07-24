from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i15.laue import LaueMonochrometer
from dodal.devices.i15.motors import NumberedTripleAxisStage
from dodal.devices.i15.multilayer_mirror import MultiLayerMirror
from dodal.devices.i15.rail import Rail
from dodal.devices.motors import XYPhiStage, XYStage, YZStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i15-1")  # Default used when not on a live beamline
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)  # Configure logging and util functions
set_utils_beamline(BL)

"""
Define device factory functions below this point.
A device factory function is any function that has a return type which conforms
to one or more Bluesky Protocols.
"""


@device_factory()
def attY() -> NumberedTripleAxisStage:
    return NumberedTripleAxisStage(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        axis1_infix="STICK1",
        axis2_infix="STICK2",
        axis3_infix="STICK3",
    )


@device_factory()
def baseY() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:Y")


@device_factory()
def blowerY() -> Motor:
    """Same motor as blowerZ"""
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


@device_factory()
def blowerZ() -> Motor:
    """Same motor as blowerY"""
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


@device_factory()
def bs2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-SMAR-02:")


@device_factory()
def clean() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-ABSB-01:CLEAN:")


@device_factory()
def det2() -> YZStage:
    return YZStage(f"{PREFIX.beamline_prefix}-EA-DET-02:")


@device_factory()
def envX() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:ENV:X")


@device_factory()
def f2y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-02:Y")


@device_factory()
def m1() -> MultiLayerMirror:
    return MultiLayerMirror(f"{PREFIX.beamline_prefix}-OP-MIRR-01:")


@device_factory()
def rail() -> Rail:
    return Rail(f"{PREFIX.beamline_prefix}-MO-RAIL-01:")


@device_factory(skip=True)
def sam() -> XYPhiStage:
    return XYPhiStage(f"{PREFIX.beamline_prefix}-MO-TABLE-01:SAMPLE:", phi_infix="PHI2")


@device_factory()
def slits_1() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def slits_2() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def slits_3() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def slits_4() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def slits_5() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def tth() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:TTH")


@device_factory()
def trans() -> XYPhiStage:
    return XYPhiStage(prefix=f"{PREFIX.beamline_prefix}-MO-TABLE-01:TRANS:")


@device_factory()
def xtal() -> LaueMonochrometer:
    return LaueMonochrometer(prefix=f"{PREFIX.beamline_prefix}-OP-LAUE-01:")
