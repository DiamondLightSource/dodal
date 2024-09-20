from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from pathlib import Path
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.adsim import SimStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, get_hostname

BL = get_hostname()
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/scratch/adsim/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)


def sim_motors(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SimStage:
    return device_instantiation(
        SimStage,
        "sim_motors",
        BL + "-MO-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False
    )


def adsim(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SimDetector:
    return device_instantiation(
        SimDetector,
        "adsim",
        BL + "-AD-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        path_provider=get_path_provider(),
        bl_prefix=False
    )
