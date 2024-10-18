from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import HDF5_PREFIX
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.linkam3 import Linkam3
from dodal.devices.slits import Slits
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("p38")
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
        Path("/dls/p38/data/2024/cm37282-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def d3() -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX.beamline_prefix}-DI-DCAM-01:",
        drv_suffix="DET:",
        hdf_suffix=HDF5_PREFIX,
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)  # Disconnected
def d11() -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX.beamline_prefix}-DI-DCAM-03:",
        drv_suffix="DET:",
        hdf_suffix=HDF5_PREFIX,
        path_provider=get_path_provider(),
    )


@device_factory()
def d12() -> AravisDetector:
    return AravisDetector(
        prefix=f"{PREFIX.beamline_prefix}-DI-DCAM-04:",
        drv_suffix="DET:",
        hdf_suffix=HDF5_PREFIX,
        path_provider=get_path_provider(),
    )


@device_factory()
def i0() -> TetrammDetector:
    return TetrammDetector(
        prefix=f"{PREFIX.beamline_prefix}-EA-XBPM-01:",
        path_provider=get_path_provider(),
    )


# Must find which PandA IOC(s) are compatible
# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@device_factory(skip=True)
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda2() -> HDFPanda:
    return HDFPanda(
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-PANDA-02:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda3() -> HDFPanda:
    return HDFPanda(
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-PANDA-03:",
        path_provider=get_path_provider(),
    )


#
# The linkam device is moved between i22 and p38 as appropriate
#


@device_factory(skip=True)
def linkam() -> Linkam3:
    return Linkam3(
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-LINKM-02:",
    )


#
# The following devices are created as fake by default since P38 has no optics,
# but having mock devices here means they will be reflected in downstream data
# processing, where they may be required.
#


@device_factory(mock=True)
def slits_1() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


@device_factory(mock=True)
def slits_2() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:")


@device_factory(mock=True)
def slits_3() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:")


@device_factory(mock=True)
def slits_4() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@device_factory(mock=True)
def slits_5() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:")


@device_factory(mock=True)
def slits_6() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:")


@device_factory(mock=True)
def fswitch() -> FSwitch:
    return FSwitch(
        prefix=f"{PREFIX.beamline_prefix}-MO-FSWT-01:",
        lens_geometry="paraboloid",
        cylindrical=True,
        lens_material="Beryllium",
    )


@device_factory(mock=True)
def vfm() -> FocusingMirror:
    return FocusingMirror(prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:VFM:")


@device_factory(mock=True)
def hfm() -> FocusingMirror:
    return FocusingMirror(prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:HFM:")


@device_factory(mock=True)
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
        motion_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-MO-DCM-01:",
        temperature_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-DCM-01:",
        crystal_1_metadata=crystal_1_metadata,
        crystal_2_metadata=crystal_2_metadata,
    )


@device_factory(mock=True)
def undulator() -> Undulator:
    return Undulator(
        prefix=f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        poles=80,
        length=2.0,
    )
