from pathlib import Path

from ophyd_async.epics.motor import Motor
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
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

"""
NOTE: Due to the CA gateway machine being switched off, PVs are not available remotely
and you need to be on the beamline network to access them.
The simplest way to do this is to `ssh i20-1-ws001` and run dodal connect i20_1 from there.
"""


@device_factory()
def turbo_slit() -> TurboSlit:
    """
    turboslit for selecting energy from the polychromator
    """

    return TurboSlit(f"{PREFIX.beamline_prefix}-OP-PCHRO-01:TS:")


@device_factory()
def turbo_slit_x() -> Motor:
    """
    turbo slit x motor
    """
    return Motor(f"{PREFIX.beamline_prefix}-OP-PCHRO-01:TS:XFINE")


@device_factory()
def panda() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-02:", path_provider=get_path_provider()
    )


# Use mock device until motors are reconnected on the beamline
@device_factory(mock=True)
def alignment_x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-STAGE-01:X")


# Use mock device until motors are reconnected on the beamline
@device_factory(mock=True)
def alignment_y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-STAGE-01:Y")


@device_factory(skip=True)
def xspress3() -> Xspress3:
    """
    16 channels Xspress3 detector
    """
    return Xspress3(
        f"{PREFIX.beamline_prefix}-EA-DET-03:",
        num_channels=16,
    )
