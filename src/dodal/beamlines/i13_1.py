from pathlib import Path

from ophyd_async.epics.areadetector.aravis import AravisDetector

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitDirectoryProvider
from dodal.devices.motors import XYZPositioner
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name


BL = get_beamline_name("i13_1")
set_log_beamline(BL)
set_utils_beamline(BL)
set_directory_provider(
    StaticVisitDirectoryProvider(
        BL,
        Path("/data/2024/cm37257-4/"),  # latest commissioning visit
    )
)


def sample_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        prefix="-MO-PI-02:",
        name="sample_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def sample_xyz_lab_fa_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        FilterMotor,
        prefix="-MO-STAGE-02:FIXANG:",
        name="sample_xyz_lab_fa_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def side_camera(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        prefix="-OP-FLOAT-03:",
        name="side_camera",
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        directory_provider=get_directory_provider(),
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
