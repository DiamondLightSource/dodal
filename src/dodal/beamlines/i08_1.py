from functools import cache
from pathlib import Path

from ophyd_async.core import (
    AutoIncrementFilenameProvider,
    PathProvider,
    StaticPathProvider,
)
from ophyd_async.epics.adandor3 import Andor3Detector
from ophyd_async.epics.adcore import ADWriterFactory, NDStatsIO
from ophyd_async.epics.pmac import PmacIO
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i08_1 import Grating
from dodal.devices.motors import XYStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i08-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
I_PREFIX = PREFIX = BeamlinePrefix(BL, suffix="I")
PATH = "/dls/i08-1/data/2026/cm44149-5/tmp/"


set_log_beamline(BL)
set_utils_beamline(BL)


devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticPathProvider(
        AutoIncrementFilenameProvider(base_filename="panda"), Path(PATH)
    )


@devices.factory()
def scanning_fine() -> XYStage:
    """Fine X and Y stages."""
    return XYStage(
        prefix=f"{PREFIX.beamline_prefix}-EA-TABLE-01:", x_infix="XF", y_infix="YF"
    )


@devices.factory()
def scanning_coarse() -> XYStage:
    """Coarse X and Y stages."""
    return XYStage(
        prefix=f"{PREFIX.beamline_prefix}-EA-TABLE-01:", x_infix="XC", y_infix="YC"
    )


@devices.factory()
def scanning_combined() -> XYStage:
    return XYStage(prefix=f"{PREFIX.beamline_prefix}-EA-TABLE-01:")


# t1j_advanced


@devices.factory()
def scanning_pmac() -> PmacIO:
    """PMac controller using running fly scans with trajectory."""
    return PmacIO(
        prefix=f"{PREFIX.beamline_prefix}-MO-STEP-01:",
        raw_motors=[scanning_fine().x, scanning_fine().y],
        coord_nums=[2],
        name="pmac",
    )


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{I_PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def panda1(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def andor_detector(path_provider: PathProvider) -> Andor3Detector:
    return Andor3Detector(
        f"{PREFIX.beamline_prefix}-EA-DET-08:",
        ADWriterFactory.hdf(path_provider=path_provider, writer_suffix=HDF5_SUFFIX),
        driver_suffix=CAM_SUFFIX,
        name="AndorMarana",
        plugins={
            "stats": NDStatsIO(prefix=f"{PREFIX.beamline_prefix}-EA-DET-08:STAT:")
        },
    )
