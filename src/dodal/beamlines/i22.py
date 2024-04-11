from ophyd_async.epics.areadetector import ADAravisDetector
from ophyd_async.epics.areadetector.drivers import ADAravisDriver
from ophyd_async.epics.areadetector.writers.nd_file_hdf import NDFileHDF

from dodal.beamlines.beamline_utils import device_instantiation, get_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i22")
set_log_beamline(BL)
set_utils_beamline(BL)


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def it(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "it",
        "-EA-TTRM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def oav_driver(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ADAravisDriver:
    return device_instantiation(
        ADAravisDriver,
        "oav_driver",
        "-DI-OAV-01:DRV:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def oav_writer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> NDFileHDF:
    return device_instantiation(
        NDFileHDF,
        "oav_writer",
        "-DI-OAV-01:HDF:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def oav(
    oav_driver: ADAravisDriver,
    oav_writer: NDFileHDF,
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> ADAravisDetector:
    return device_instantiation(
        ADAravisDetector,
        "oav",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
        driver=oav_driver,
        hdf=oav_writer
    )
