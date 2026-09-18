"""Beamline module for the t11 standalone simulation.

A copy of ``dodal.beamlines.adsim`` with the prefix moved from ``t01``
(``BL01T``) to ``t11`` (``BL11T``) so that it matches the IOCs deployed by
t11-services:

    services/bl11t-mo-sim-01   motorSim.simMotorController  BL11T-MO-SIMC-01:
                               axes M1 (x) and M2 (theta)
    services/bl11t-di-cam-01   ADSimDetector.simDetector    BL11T-DI-CAM-01:
                               driver suffix DRV, HDF5 writer suffix HDF5
"""

from ophyd_async.epics.adcore import ADWriterFactory
from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import HDF5_SUFFIX
from dodal.device_manager import DeviceManager
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "t11"
PREFIX = BeamlinePrefix("t11")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
def path_provider():
    # Only used if a path_provider is not passed to the device manager when the
    # devices are built. Under blueAPI with numtracker enabled, numtracker
    # takes priority and this is not created.
    from pathlib import Path

    from ophyd_async.core import StaticPathProvider, UUIDFilenameProvider

    return StaticPathProvider(
        UUIDFilenameProvider(),
        Path("/tmp"),
    )


@devices.factory()
def stage() -> XThetaStage:
    return XThetaStage(
        f"{PREFIX.beamline_prefix}-MO-SIMC-01:", x_infix="M1", theta_infix="M2"
    )


@devices.factory()
def det(path_provider) -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        ADWriterFactory.hdf(path_provider=path_provider, writer_suffix=HDF5_SUFFIX),
        driver_suffix="DRV:",
    )
