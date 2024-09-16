from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("c01", force_default=True)  # noqa: F821
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/b01-1/data/"),
        client=LocalDirectoryServiceClient(),
    )
)


def panda(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> HDFPanda:
    return device_instantiation(
        device_factory=HDFPanda,
        name="panda",
        prefix="-EA-PANDA-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


def synchrotron(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Synchrotron:
    return device_instantiation(
        Synchrotron,
        "synchrotron",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def manta(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "manta",
        "-DI-DCAM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
    )
