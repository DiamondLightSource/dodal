from pathlib import Path

from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import numbered_slits
from dodal.common.crystal_metadata import CrystalMetadata
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.KBMirror import KBMirror
from dodal.devices.i18.sim_detector import SimDetector
from dodal.devices.i18.sim_raster_stage import RasterStage
from dodal.devices.i18.table import Table
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

BL = get_beamline_name("i18")
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
        Path("/dls/i18/data/2024/cm37264-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
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
    )


@skip_device()
def undulator(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Undulator:
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        poles=80,
        length=2.0,
    )


@skip_device()
def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        1,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@skip_device()
def panda1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda1",
        "-MO-PANDA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


def old_xspress3(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Xspress3:
    return device_instantiation(
        Xspress3,
        prefix="-EA-XSP-02:",
        name="Xspress3",
        num_channels=16,
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


# NOTE: the reason for skipping is that the odin detectors are not yet supported
# There is a controls project in the works, not ready anytime soon
@skip_device()
def xspress3_odin(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Xspress3:
    return device_instantiation(
        Xspress3,
        prefix="-EA-XSP-03:",
        name="Xspress3",
        num_channels=4,
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


crystal_1_metadata = CrystalMetadata("Si111")
crystal_2_metadata = CrystalMetadata("Si111")

_unused_crystal_metadata_1 = CrystalMetadata("Si311")
_unused_crystal_metadata_2 = CrystalMetadata("Si333")


def dcm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> DoubleCrystalMonochromator:
    return device_instantiation(
        DoubleCrystalMonochromator,
        "dcm",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        motion_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-MO-DCM-01:",
        temperature_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-DCM-01:",
        crystal_1_metadata=crystal_1_metadata,
        crystal_2_metadata=crystal_2_metadata,
    )


@skip_device()
def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-DI-XBPM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        type="Cividec Diamond XBPM",
        path_provider=get_path_provider(),
    )


@skip_device()
def it(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "it",
        "-DI-XBPM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        type="Tetramm",
        path_provider=get_path_provider(),
    )


@skip_device
def vfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> KBMirror:
    return device_instantiation(
        KBMirror,
        "vfm",
        "-OP-VFM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def hfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> KBMirror:
    return device_instantiation(
        KBMirror,
        "hfm",
        "-OP-HFM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def diode(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Diode:
    return device_instantiation(
        Diode,
        "diodad7bdiode",
        "-DI-PHDGN-07:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def table(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Table:
    return device_instantiation(
        Table,
        "table",
        "-MO-TABLE-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


# note this is a mock table, not sure how does it relate to the real Table,
# maybe just a fake option in instantiation is needed
@skip_device()
def raster_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> RasterStage:
    return device_instantiation(
        RasterStage,
        "raster_stage",
        "-MO-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def sim_detector(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False):
    return device_instantiation(
        SimDetector,
        "sim_detector",
        "-MO-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
