from pathlib import Path

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.turbo_slit import TurboSlit
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i20-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


# Currently we must hard-code the visit, determining the visit at runtime requires
# infrastructure that is still WIP.
# Communication with GDA is also WIP so for now we determine an arbitrary scan number
# locally and write the commissioning directory. The scan number is not guaranteed to
# be unique and the data is at risk - this configuration is for testing only.
set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/i20-1/data/2023/cm33897-5/bluesky"),
        client=RemoteDirectoryServiceClient("http://i20-1-control:8088/api"),
    )
)


# NOTE this is mock as we cannot move items on the beamline until we get sign-off to do so
@device_factory(mock=True)
def turbo_slit() -> TurboSlit:
    """
    turboslit for selecting energy from the polychromator
    """

    return TurboSlit(f"{PREFIX.beamline_prefix}-OP-PCHRO-01:TS:")


@device_factory(skip=True)
def xspress3() -> Xspress3:
    """
    16 channels Xspress3 detector
    """

    return Xspress3(
        f"{PREFIX.beamline_prefix}-EA-DET-03:",
        num_channels=16,
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()
