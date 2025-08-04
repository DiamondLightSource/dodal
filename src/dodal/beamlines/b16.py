from pathlib import Path

from ophyd_async.epics.adcore import (
    AreaDetector,
)
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.b16.detector import (
    software_triggered_tiff_area_detector,
)
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b16")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/b16/data/2025/cm40635-3/bluesky"),
        client=RemoteDirectoryServiceClient("http://b16-control:8088/api"),
    )
)


@device_factory()
def attol1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT0")


@device_factory()
def attol2() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT1")


@device_factory()
def attol3() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-03:ACT2")


@device_factory()
def attorot1() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-EA-ECC-02:ACT2")


@device_factory()
def fds2() -> AreaDetector:
    prefix = f"{PREFIX.beamline_prefix}-EA-FDS-02:"
    return software_triggered_tiff_area_detector(prefix)


@device_factory()
def sim_stage() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-SIM-01:",
        x_infix="M1",
        y_infix="M2",
        z_infix="M3",
    )
