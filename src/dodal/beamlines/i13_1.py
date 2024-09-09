from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitPathProvider
from dodal.devices.motors import XYZPositioner
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i13-1")
set_log_beamline(BL)
set_utils_beamline(BL)
set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/data/2024/cm37257-4/"),  # latest commissioning visit
    )
)


def sample_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        XYZPositioner,
        prefix="BL13J-MO-PI-02:",
        name="sample_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def sample_xyz_lab_fa_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        XYZPositioner,
        prefix="BL13J-MO-PI-02:FIXANG:",
        name="sample_xyz_lab_fa_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def side_camera(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        prefix="BL13J-OP-FLOAT-03:",
        name="side_camera",
        bl_prefix=False,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        path_provider=get_path_provider(),
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
