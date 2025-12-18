from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.adcore import NDROIStatIO
from ophyd_async.epics.pmac import PmacIO
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    get_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.device_manager import DeviceManager
from dodal.devices.motors import XYZStage
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "b01-1"
# TODO: Should not have to provide suffix.
# Make issue for this.
PREFIX = BeamlinePrefix(BL, suffix="C")
set_log_beamline(BL)
set_utils_beamline(BL)
devices = DeviceManager()

"""
NOTE: Due to ArgoCD and the k8s cluster configuration those PVs are not available remotely.
You need to be on the beamline-local network to access them.
The simplest way to do this is to `ssh b01-1-ws001` and run `dodal connect b01_1` from there.
remember about the underscore in the beamline name.

See the IOC status here:
https://argocd.diamond.ac.uk/applications?showFavorites=false&proj=&sync=&autoSync=&health=&namespace=&cluster=&labels=
"""


@devices.factory()
def pandabrick() -> HDFPanda:
    """Provides triggering of the detectors.

    Returns:
        HDFPanda: The HDF5-based detector trigger device.
    """
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PPANDA-01:",
        path_provider=get_path_provider(),
    )


@devices.factory()
def pandabox() -> HDFPanda:
    """Provides triggering of the detectors.

    Returns:
        HDFPanda: The HDF5-based detector trigger device.
    """
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def spectroscopy_detector() -> AravisDetector:
    """The Manta camera for the spectroscopy experiment.

    Looks at the spectroscopy screen and visualises light
    transmitted through the sample after it has gone through
    the diffraction grating.

    Returns:
        AravisDetector: The spectroscopy camera device.
    """
    pv_prefix = f"{PREFIX.beamline_prefix}-DI-DCAM-02:"
    return AravisDetector(
        pv_prefix,
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        plugins={
            "roistat": NDROIStatIO(f"{pv_prefix}ROISTAT:", num_channels=3),
        },
    )


@devices.factory()
def imaging_detector() -> AravisDetector:
    """The Mako camera for the imaging experiment.

    Looks at the on-axis viewing screen.

    Returns:
        AravisDetector: The imaging camera device.
    """
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-DI-DCAM-01:",
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@devices.factory()
def sample_stage() -> XYZStage:
    """An XYZ stage holding the sample.

    Returns:
        XYZStage: The XYZ sample stage device.
    """
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-PPMAC-01:",
    )


@devices.factory()
def pmac() -> PmacIO:
    """A Power PMAC.

    Returns:
        PmacIO: IO interface for the Power PMAC.
    """
    sample_stage = XYZStage(
        f"{PREFIX.beamline_prefix}-MO-PPMAC-01:",
    )
    return PmacIO(
        prefix=f"{PREFIX.beamline_prefix}-MO-PPMAC-01:",
        raw_motors=[sample_stage.y, sample_stage.x],
        coord_nums=[1],
    )
