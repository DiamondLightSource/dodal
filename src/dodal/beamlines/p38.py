from ophyd_async.epics.areadetector import ADAravisDetector
from ophyd_async.epics.areadetector.drivers import ADAravisDriver
from ophyd_async.epics.areadetector.writers import NDFileHDF

from dodal.beamlines.beamline_utils import device_instantiation, get_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("p38")
set_log_beamline(BL)
set_utils_beamline(BL)


def d11_driver(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ADAravisDriver:
    return device_instantiation(
        ADAravisDriver,
        "d11_driver",
        "-DI-DCAM-03:DRV:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d11_writer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> NDFileHDF:
    return device_instantiation(
        NDFileHDF,
        "d11_writer",
        "-DI-DCAM-03:HDF:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d11(
    d11_driver: ADAravisDriver,
    d11_writer: NDFileHDF,
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> ADAravisDetector:
    return device_instantiation(
        ADAravisDetector,
        "D11",
        "-DI-DCAM-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
        driver=d11_driver,
        hdf=d11_writer,
    )


def d12_driver(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ADAravisDriver:
    return device_instantiation(
        ADAravisDriver,
        "d12_driver",
        "-DI-DCAM-04:DRV:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d12_writer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> NDFileHDF:
    return device_instantiation(
        NDFileHDF,
        "d12_writer",
        "-DI-DCAM-04:HDF:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def d12(
    d12_driver: ADAravisDriver,
    d12_writer: NDFileHDF,
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> ADAravisDetector:
    return device_instantiation(
        ADAravisDetector,
        "D12",
        "-DI-DCAM-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
        driver=d12_driver,
        hdf=d12_writer,
    )


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )
