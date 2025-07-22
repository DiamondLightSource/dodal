from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
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
def att1y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-01:STICK1")


@device_factory()
def att2y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-01:STICK2")


@device_factory()
def att3y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-01:STICK3")


@device_factory()
def blowerY() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


@device_factory()
def blowerZ() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


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
def m1ds_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:X2")


@device_factory()
def m1ds_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:J3")


@device_factory()
def m1ib_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:J1")


@device_factory()
def m1ob_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:J2")


@device_factory()
def m1pitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:PITCH")


@device_factory()
def m1roll() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:ROLL")


@device_factory()
def m1us_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:X1")


@device_factory()
def m1x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:X")


@device_factory()
def m1y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:Y")


@device_factory()
def m1yaw() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-MIRR-01:YAW")


@device_factory()
def rail_pitch() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-RAIL-01:PITCH")


@device_factory()
def rail_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-RAIL-01:Y")


@device_factory()
def rail_y1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-RAIL-01:Y1")


@device_factory()
def rail_y2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-RAIL-01:Y2")


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
def trans() -> XYPhiStage:
    return XYPhiStage(prefix=f"{PREFIX.beamline_prefix}-MO-TABLE-01:TRANS:")


@device_factory(skip=BL == "i15-1")
def synchrotron() -> Synchrotron:
    return Synchrotron()
