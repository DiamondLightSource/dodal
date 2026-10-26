from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider, StaticPathProvider, UUIDFilenameProvider
from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.adcore import ADWriterFactory
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import HDF5_SUFFIX
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i11.dcm import DCM
from dodal.devices.beamlines.i11_1.stages import LargeStage1
from dodal.devices.slits import SlitsWithIndividualBlades
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i11-1")
PREFIX = "BL11J"
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticPathProvider(UUIDFilenameProvider(), Path("/tmp"))


@devices.factory()
def large_stage_x_translation() -> Motor:
    """This is intentionally seperate from large stage 1 and large stage 2."""
    return Motor(prefix=f"{PREFIX}-MO-LSLID-01:X:POSN")


@devices.factory()
def large_stage_y_lifting() -> Motor:
    """This is just a lifting stage."""
    return Motor(prefix=f"{PREFIX}-MO-LIFT-01:Y")


@devices.factory()
def large_stage_1() -> LargeStage1:
    prefix = f"{PREFIX}-MO-GONIO-01:"
    return LargeStage1(prefix=prefix)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def dcm() -> DCM:
    return DCM(
        prefix=f"{PREFIX}-MO-DCM-01:",
        xtal_prefix=f"{PREFIX}-DI-DCM-01:",
    )


@devices.factory()
def slits_6() -> SlitsWithIndividualBlades:
    return SlitsWithIndividualBlades(prefix=f"{PREFIX}-AL-SLITS-06:")


@devices.factory()
def slits_7() -> SlitsWithIndividualBlades:
    return SlitsWithIndividualBlades(prefix=f"{PREFIX}-AL-SLITS-07:")


@devices.factory()
def dcam3(path_provider: PathProvider) -> AravisDetector:
    pv_prefix = f"{PREFIX}-DI-DCAM-03:"
    return AravisDetector(
        pv_prefix,
        ADWriterFactory.hdf(path_provider=path_provider, writer_suffix=HDF5_SUFFIX),
        driver_suffix="CAM:",
    )


@devices.factory()
def dcam4(path_provider: PathProvider) -> AravisDetector:
    pv_prefix = f"{PREFIX}-DI-DCAM-04:"
    return AravisDetector(
        pv_prefix,
        ADWriterFactory.hdf(path_provider=path_provider, writer_suffix=HDF5_SUFFIX),
        driver_suffix="CAM:",
    )


# TODO: Add the perkin elmer as a detector!
# @devices.factory()
# def perkin_elmer() -> PerkinElmer:
#     return PerkinElmer(prefix=f"{PREFIX}-EA-DET-02:")
