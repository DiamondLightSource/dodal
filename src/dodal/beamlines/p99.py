from pathlib import Path

from ophyd_async.core import AutoIncrementFilenameProvider, StaticPathProvider
from ophyd_async.epics.adcore import SingleTriggerDetector

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    set_beamline,
)
from dodal.devices.areadetector import Andor2
from dodal.devices.motors import XYZPositioner
from dodal.devices.p99.sample_stage import FilterMotor, SampleAngleStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("BL99P")
set_log_beamline(BL)
set_beamline(BL)


def sample_angle_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SampleAngleStage:
    """Sample stage for p99"""

    return device_instantiation(
        SampleAngleStage,
        prefix="-MO-STAGE-01:",
        name="sample_angle_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def sample_stage_filer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> FilterMotor:
    """Sample stage for p99"""

    return device_instantiation(
        FilterMotor,
        prefix="-MO-STAGE-02:MP:SELECT",
        name="sample_stage_filer",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def sample_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        XYZPositioner,
        prefix="-MO-STAGE-02:",
        name="sample_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def sample_lab_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    return device_instantiation(
        XYZPositioner,
        prefix="-MO-STAGE-02:LAB:",
        name="sample_lab_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


andor_data_path = StaticPathProvider(
    filename_provider=AutoIncrementFilenameProvider(base_filename="andor2"),
    directory_path=Path("/dls/p99/data/2024/cm37284-2/processing/writenData"),
)


def andor2_det(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Andor2:
    return device_instantiation(
        Andor2,
        prefix="-EA-DET-03:",
        name="andor2_det",
        path_provider=andor_data_path,
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def andor2_point(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SingleTriggerDetector:
    return device_instantiation(
        SingleTriggerDetector,
        drv=andor2_det().drv,
        read_uncached=([andor2_det().drv.stat_mean]),
        prefix="",
        name="andor2_point",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
