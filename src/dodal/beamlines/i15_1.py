from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.epics.adcore import ADJPEGWriter, ContAcqAreaDetector
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX
from dodal.common.visit import StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i15.laue import LaueMonochrometer
from dodal.devices.beamlines.i15.motors import NumberedTripleAxisStage
from dodal.devices.beamlines.i15.multilayer_mirror import MultiLayerMirror
from dodal.devices.beamlines.i15.rail import Rail
from dodal.devices.beamlines.i15_1.attenuator import Attenuator
from dodal.devices.beamlines.i15_1.gonio_interlock import GonioInterlock
from dodal.devices.beamlines.i15_1.puck_detector import PuckDetect
from dodal.devices.beamlines.i15_1.robot import Robot
from dodal.devices.hutch_shutter import (
    HutchInterlock,
    InterlockedHutchShutter,
    PLCShutterInterlock,
)
from dodal.devices.motors import XYPhiStage, XYStage, XYZStage, YZStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i15-1")  # Default used when not on a live beamline
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)  # Configure logging and util functions
set_utils_beamline(BL)

devices = DeviceManager()
"""
Define device factory functions below this point.
A device factory function is any function that has a return type which conforms
to one or more Bluesky Protocols.
"""


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/dls/i15-1/data/2026/cm44163-2/"),
    )


@devices.factory()
def att_y() -> NumberedTripleAxisStage:
    return NumberedTripleAxisStage(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        axis1_infix="STICK1",
        axis2_infix="STICK2",
        axis3_infix="STICK3",
    )


@devices.factory()
def base_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:Y")


@devices.factory()
def blower_y() -> Motor:
    """Same motor as blowerZ."""
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


@devices.factory()
def blower_z() -> Motor:
    """Same motor as blowerY."""
    return Motor(f"{PREFIX.beamline_prefix}-EA-BLOWR-01:TLATE")


@devices.factory()
def bs2() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-SMAR-02:")


@devices.factory(skip=True)  # Currently turned off due to work on the beamline
def clean() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-ABSB-01:CLEAN:")


@devices.factory()
def det2() -> YZStage:
    return YZStage(f"{PREFIX.beamline_prefix}-EA-DET-02:")


@devices.factory()
def env_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:ENV:X")


@devices.factory()
def f2y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-02:Y")


@devices.factory()
def hexapod() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-HEX-01:",
    )


@devices.factory()
def hexapod_rotation() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-HEX-01:",
        x_infix="RX",
        y_infix="RY",
        z_infix="RZ",
    )


@devices.factory()
def m1() -> MultiLayerMirror:
    return MultiLayerMirror(f"{PREFIX.beamline_prefix}-OP-MIRR-01:")


@devices.factory()
def rail() -> Rail:
    return Rail(f"{PREFIX.beamline_prefix}-MO-RAIL-01:")


@devices.factory(skip=True)
def sam() -> XYPhiStage:
    return XYPhiStage(f"{PREFIX.beamline_prefix}-MO-TABLE-01:SAMPLE:", phi_infix="PHI2")


@devices.factory(skip=True)  # Currently turned off due to work on the beamline
def slits_1() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@devices.factory()
def slits_2() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@devices.factory()
def slits_3() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@devices.factory()
def slits_4() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@devices.factory()
def slits_5() -> Slits:
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def tth() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:TTH")


@devices.factory()
def trans() -> XYPhiStage:
    return XYPhiStage(prefix=f"{PREFIX.beamline_prefix}-MO-TABLE-01:TRANS:")


@devices.factory(skip=True)  # Currently turned off due to work on the beamline
def xtal() -> LaueMonochrometer:
    return LaueMonochrometer(prefix=f"{PREFIX.beamline_prefix}-OP-LAUE-01:")


@devices.factory()
def robot() -> Robot:
    return Robot(
        robot_prefix=f"{PREFIX.beamline_prefix}-MO-ROBOT-01:",
        current_sample_prefix=f"{PREFIX.beamline_prefix}-EA-LOC-01:",
    )


@devices.factory()
def puck_detect() -> PuckDetect:
    return PuckDetect("https://i15-1-cam3-processing.diamond.ac.uk/result")


@devices.factory()
def attenuator() -> Attenuator:
    return Attenuator(f"{PREFIX.beamline_prefix}-OP-ATTN-02:")


@devices.factory()
def hutch_interlock() -> HutchInterlock:
    return HutchInterlock(bl_prefix="BL15I", interlock_suffix="-PS-IOC-02:M11:LOP")


@devices.factory()
def hutch_shutter() -> InterlockedHutchShutter:
    return InterlockedHutchShutter(
        bl_prefix=PREFIX.beamline_prefix,
        interlock=PLCShutterInterlock(
            bl_prefix=PREFIX.beamline_prefix, interlock_suffix="-PS-SHTR-01:ILKSTA"
        ),
    )


@devices.factory()
def gonio_interlock() -> GonioInterlock:
    return GonioInterlock(
        bl_prefix=PREFIX.beamline_prefix, interlock_suffix="-VA-OMRON-01:INT3:ILK"
    )


@devices.factory()
def webcam_1(path_provider: PathProvider) -> ContAcqAreaDetector:
    return ContAcqAreaDetector(
        f"{PREFIX.beamline_prefix}-DI-WEB-01:",
        path_provider=path_provider,
        drv_suffix=CAM_SUFFIX,
        cb_suffix="CIRC:",
        writer_cls=ADJPEGWriter,
        fileio_suffix="JPEG:",
    )


@devices.factory()
def webcam_2(path_provider: PathProvider) -> ContAcqAreaDetector:
    return ContAcqAreaDetector(
        f"{PREFIX.beamline_prefix}-DI-WEB-02:",
        path_provider=path_provider,
        drv_suffix=CAM_SUFFIX,
        cb_suffix="CIRC:",
        writer_cls=ADJPEGWriter,
        fileio_suffix="JPEG:",
    )


@devices.factory()
def cam_1(path_provider: PathProvider) -> ContAcqAreaDetector:
    return ContAcqAreaDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=path_provider,
        drv_suffix=CAM_SUFFIX,
        cb_suffix="CIRC:",
        writer_cls=ADJPEGWriter,
        fileio_suffix="JPEG:",
    )


@devices.factory()
def cam_2(path_provider: PathProvider) -> ContAcqAreaDetector:
    return ContAcqAreaDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-02:",
        path_provider=path_provider,
        drv_suffix=CAM_SUFFIX,
        cb_suffix="CIRC:",
        writer_cls=ADJPEGWriter,
        fileio_suffix="JPEG:",
    )


@devices.factory()
def cam_3(path_provider: PathProvider) -> ContAcqAreaDetector:
    return ContAcqAreaDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-03:",
        path_provider=path_provider,
        drv_suffix=CAM_SUFFIX,
        cb_suffix="CIRC:",
        writer_cls=ADJPEGWriter,
        fileio_suffix="JPEG:",
    )
