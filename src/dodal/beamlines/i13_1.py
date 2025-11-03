from pathlib import Path

from ophyd_async.core import (  # noqa: F401
    AutoIncrementFilenameProvider,
    StaticPathProvider,
    UUIDFilenameProvider,
)
from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.motor import Motor
from ophyd_async.epics.pmac import PmacIO
from ophyd_async.fastcs.panda import HDFPanda

import dodal.log
from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (  # noqa: F401
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.i13_1.merlin import Merlin
from dodal.devices.motors import XYZStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

print(f"Logging level = {dodal.log.LOGGER.level}")

# get_beamline_name with no arguments to get the default BL name (from $BEAMLINE)
BL = get_beamline_name("i13-1")
set_log_beamline(BL)
set_utils_beamline(BL)

PREFIX = BeamlinePrefix(BL, "J")
PATH = "/dls/i13-1/data/2025/cm40629-5/tmp"

static_path = StaticPathProvider(UUIDFilenameProvider(), Path(PATH))

# set_path_provider(
#     StaticVisitPathProvider(
#         BL,
#         Path(PATH),
#         # client=RemoteDirectoryServiceClient("http://i13-1-control:8088/api"),
#         client=LocalDirectoryServiceClient(),
#     )
# )
# path_test = get_path_provider()
# # print(path_test._root)  # type: ignore
set_path_provider(
    StaticPathProvider(
        # UUIDFilenameProvider(),
        # AutoIncrementFilenameProvider("merlin_test"),
        AutoIncrementFilenameProvider("merlin_test", starting_value=1, max_digits=3),
        Path(PATH),
    )
)
path_test = get_path_provider()
print(f"Data path = {path_test._directory_path}")  # type: ignore # noqa
print(f"Merlin base filename = {path_test._filename_provider._base_filename}")  # type: ignore # noqa


# --------------------------------------------------------------------------
# Individual and Combined Motors/Stages
# -------------------------------------
# Just for testing but need to be careful don't move too much.
# Have set limits to 0-1mm.
@device_factory()
def mirror02_vert_y() -> Motor:
    return Motor(prefix=f"{PREFIX.beamline_prefix}-OP-MIRR-02:VERT:Y")


@device_factory()
def theta() -> Motor:
    return Motor(prefix=f"{PREFIX.beamline_prefix}-MO-STAGE-01:THETA")


@device_factory()
def theta_virtual() -> Motor:
    return Motor(prefix=f"{PREFIX.beamline_prefix}-MO-PI-02:VIRTUAL:THETA")


@device_factory()
def sample_xyz() -> XYZStage:
    return XYZStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-PI-02:",
        name="sample_xyz",
        x_infix="X",
        y_infix="Y",
        z_infix="Z",
    )


async def sample_xyz_print():
    pi = sample_xyz()
    x_pos = await pi.x.read()
    y_pos = await pi.y.read()
    z_pos = await pi.z.read()
    print(
        x_pos["sample_xyz-x"]["value"],
        y_pos["sample_xyz-y"]["value"],
        z_pos["sample_xyz-z"]["value"],
    )


# CS 3 can't be used with traj motion progs.
@device_factory()
def sample_xyz_lab() -> XYZStage:
    return XYZStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-PI-02:LAB:",
        name="sample_xyz_lab",
        x_infix="X",
        y_infix="Y",
        z_infix="Z",
    )


async def sample_xyz_lab_print():
    pi = sample_xyz_lab()
    x_pos = await pi.x.read()
    y_pos = await pi.y.read()
    z_pos = await pi.z.read()
    print(
        x_pos["sample_xyz_lab-x"]["value"],
        y_pos["sample_xyz_lab-y"]["value"],
        z_pos["sample_xyz_lab-z"]["value"],
    )


@device_factory()
def sample_xyz_map() -> XYZStage:
    return XYZStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-PI-02:MAP:",
        name="sample_xyz_map",
        x_infix="X",
        y_infix="Y",
        z_infix="Z",
    )


async def sample_xyz_map_print():
    pi = sample_xyz_map()
    x_pos = await pi.x.read()
    y_pos = await pi.y.read()
    z_pos = await pi.z.read()
    print(
        x_pos["sample_xyz_map-x"]["value"],
        y_pos["sample_xyz_map-y"]["value"],
        z_pos["sample_xyz_map-z"]["value"],
    )


@device_factory()
def sample_xyz_map_fa() -> XYZStage:
    return XYZStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-PI-02:FIXANG:",
        name="sample_xyz_map_fa",
        x_infix="X",
        y_infix="Y",
        z_infix="Z",
    )


async def sample_xyz_map_fa_print():
    pi = sample_xyz_map_fa()
    x_pos = await pi.x.read()
    y_pos = await pi.y.read()
    z_pos = await pi.z.read()
    print(
        x_pos["sample_xyz_map_fa-x"]["value"],
        y_pos["sample_xyz_map_fa-y"]["value"],
        z_pos["sample_xyz_map_fa-z"]["value"],
    )


# --------------------------------------------------------------------------
# PMAC and Pandas
# -------------------------------------
@device_factory()
def step_25() -> PmacIO:
    return PmacIO(
        prefix="BL13J-MO-STEP-25:",
        raw_motors=[sample_xyz().x, sample_xyz().y, sample_xyz().z, theta()],
        # coord_nums=[1],
        coord_nums=[4],
        # coord_nums=[5],
        name="step_25",
    )


@device_factory()
def panda_01() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def panda_02() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-TS-PANDA-02:",
        # path_provider=get_path_provider(),
        path_provider=static_path,
    )


# --------------------------------------------------------------------------
# Detectors
# -------------------------------------
@device_factory()
def side_camera() -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX.beamline_prefix}-OP-FLOAT-03:",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=get_path_provider(),
    )


@device_factory()
def merlin() -> Merlin:
    return Merlin(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-04:",
        drv_suffix="CAM:",
        fileio_suffix="HDF5:",
        path_provider=static_path,
    )
