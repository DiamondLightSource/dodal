from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.adpilatus import PilatusDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, DET_SUFFIX, HDF5_SUFFIX
from dodal.common.crystal_metadata import (
    MaterialsEnum,
    make_crystal_metadata_from_material,
)
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.bimorph_mirror import BimorphMirror
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.dcm import DCM
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasOAV, NXSasPilatus
from dodal.devices.linkam3 import Linkam3
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.devices.watsonmarlow323_pump import WatsonMarlow323Pump
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i22")
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
        Path("/dls/i22/data/2024/cm37271-2/bluesky"),
        client=RemoteDirectoryServiceClient("http://i22-control:8088/api"),
    )
)


@device_factory()
def saxs() -> PilatusDetector:
    metadata_holder = NXSasMetadataHolder(
        x_pixel_size=(1.72e-1, "mm"),
        y_pixel_size=(1.72e-1, "mm"),
        description="Dectris Pilatus3 2M",
        type="Photon Counting Hybrid Pixel",
        sensor_material="silicon",
        sensor_thickness=(0.45, "mm"),
        distance=(4711.833684146172, "mm"),
    )
    return NXSasPilatus(
        prefix=f"{PREFIX.beamline_prefix}-EA-PILAT-01:",
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        metadata_holder=metadata_holder,
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def waxs() -> PilatusDetector:
    metadata_holder = NXSasMetadataHolder(
        x_pixel_size=(1.72e-1, "mm"),
        y_pixel_size=(1.72e-1, "mm"),
        description="Dectris Pilatus3 2M",
        type="Photon Counting Hybrid Pixel",
        sensor_material="silicon",
        sensor_thickness=(0.45, "mm"),
        distance=(175.4199417092314, "mm"),
    )
    return NXSasPilatus(
        prefix=f"{PREFIX.beamline_prefix}-EA-PILAT-03:",
        path_provider=get_path_provider(),
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        metadata_holder=metadata_holder,
    )


@device_factory()
def i0() -> TetrammDetector:
    return TetrammDetector(
        prefix=f"{PREFIX.beamline_prefix}-EA-XBPM-02:",
        path_provider=get_path_provider(),
        type="Cividec Diamond XBPM",
    )


@device_factory()
def it() -> TetrammDetector:
    return TetrammDetector(
        prefix=f"{PREFIX.beamline_prefix}-EA-TTRM-02:",
        path_provider=get_path_provider(),
        type="PIN Diode",
    )


@device_factory()
def vfm() -> FocusingMirror:
    return FocusingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:VFM:",
    )


@device_factory()
def hfm() -> FocusingMirror:
    return FocusingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:HFM:",
    )


@device_factory()
def bimorph_hfm() -> BimorphMirror:
    return BimorphMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:G0:", number_of_channels=12
    )


@device_factory()
def bimorph_vfm() -> BimorphMirror:
    return BimorphMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-KBM-01:G1:", number_of_channels=16
    )


@device_factory()
def dcm() -> DCM:
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        temperature_prefix=f"{PREFIX.beamline_prefix}-DI-DCM-01:",
        crystal_1_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
        crystal_2_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
    )


@device_factory()
def undulator() -> Undulator:
    return Undulator(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        id_gap_lookup_table_path="/dls_sw/i22/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
        poles=80,
        length=2.0,
    )


@device_factory()
def slits_1() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


@device_factory()
def slits_2() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:")


@device_factory()
def slits_3() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:")


@device_factory()
def slits_4() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@device_factory()
def slits_5() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:")


@device_factory()
def slits_6() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:")


@device_factory()
def fswitch() -> FSwitch:
    return FSwitch(
        prefix=f"{PREFIX.beamline_prefix}-MO-FSWT-01:",
        lens_geometry="paraboloid",
        cylindrical=True,
        lens_material="Beryllium",
    )


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda2() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-02:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda3() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-03:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
def panda4() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-04:",
        path_provider=get_path_provider(),
    )


@device_factory()
def oav() -> AravisDetector:
    metadata_holder = NXSasMetadataHolder(
        x_pixel_size=(3.45e-3, "mm"),  # Double check this figure
        y_pixel_size=(3.45e-3, "mm"),
        description="AVT Mako G-507B",
        distance=(-1.0, "m"),
    )
    return NXSasOAV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        path_provider=get_path_provider(),
        metadata_holder=metadata_holder,
    )


@device_factory(skip=True)
def linkam() -> Linkam3:
    return Linkam3(prefix=f"{PREFIX.beamline_prefix}-EA-TEMPC-05:")


@device_factory()
def ppump() -> WatsonMarlow323Pump:
    """Sample Environment Peristaltic Pump"""
    return WatsonMarlow323Pump(f"{PREFIX.beamline_prefix}-EA-PUMP-01:")
