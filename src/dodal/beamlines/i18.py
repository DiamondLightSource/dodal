from pathlib import Path

from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.KBMirror import KBMirror
from dodal.devices.i18.table import Table
from dodal.devices.i18.thor_labs_stage import ThorLabsStage
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i18")
PREFIX = BeamlinePrefix(BL)
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


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# not ready yet
@device_factory(skip=True)
def undulator() -> Undulator:
    return Undulator(f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def slits_1() -> Slits:
    return Slits(f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )


# odin detectors are not yet supported.
# There is a controls project in the works,
# not ready anytime soon
@device_factory(skip=True)
def xspress3_odin() -> Xspress3:
    return Xspress3(
        f"{PREFIX.beamline_prefix}-EA-XSP-02:",
        num_channels=4,
    )


@device_factory(skip=True)
def dcm() -> DoubleCrystalMonochromator:
    crystal_1_metadata = CrystalMetadata(
        usage="Bragg",
        type="silicon",
        reflection=(1, 1, 1),
        d_spacing=(3.13475, "nm"),
    )

    crystal_2_metadata = CrystalMetadata(
        usage="Bragg",
        type="silicon",
        reflection=(1, 1, 1),
        d_spacing=(3.13475, "nm"),
    )

    return DoubleCrystalMonochromator(
        temperature_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-DCM-01:",
        crystal_1_metadata=crystal_1_metadata,
        crystal_2_metadata=crystal_2_metadata,
    )


@device_factory()
def i0() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-02:",
        path_provider=get_path_provider(),
    )


@device_factory()
def it() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def vfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-VFM-01:")


@device_factory()
def hfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@device_factory()
def d7diode() -> Diode:
    return Diode(f"{PREFIX.beamline_prefix}-DI-PHDGN-07:")


@device_factory()
def main_table() -> Table:
    return Table(f"{PREFIX.beamline_prefix}-MO-TABLE-01:")


@device_factory()
def thor_labs_stage() -> ThorLabsStage:
    return ThorLabsStage(f"{PREFIX.beamline_prefix}-MO-TABLE-02:")
