from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.motors import XYZPositioner
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "c01"
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/b01-1/data/"),
        client=LocalDirectoryServiceClient(),
    )
)

"""
NOTE: Due to ArgoCD and the k8s cluster configuration those PVs are not available remotely.
You need to be on the beamline-local network to access them.
The simplest way to do this is to `ssh b01-1-ws001` and run `dodal connect b01_1` from there.
remember about the underscore in the beamline name.

See the IOC status here:
https://argocd.diamond.ac.uk/applications?showFavorites=false&proj=&sync=&autoSync=&health=&namespace=&cluster=&labels=
"""


@device_factory()
def panda() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def manta() -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-DI-DCAM-02:",
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@device_factory()
def sample_stage() -> XYZPositioner:
    return XYZPositioner(
        f"{PREFIX.beamline_prefix}-MO-PPMAC-01:",
    )
