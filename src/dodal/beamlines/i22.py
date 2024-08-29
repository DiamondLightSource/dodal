from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.adpilatus import PilatusDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import numbered_slits
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from ophyd_async.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    get_directory_provider,
    set_directory_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_factory import device_factory
from dodal.common.beamlines.device_helpers import numbered_slits
from dodal.common.visit import DirectoryServiceClient, StaticVisitDirectoryProvider
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasOAV, NXSasPilatus
from dodal.devices.linkam3 import Linkam3
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i22")
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
def saxs():
    """Create a SAXS detector with specific settings."""
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
        prefix="-EA-PILAT-01:",
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        metadata_holder=metadata_holder,
        path_provider=get_path_provider()
    )


@device_factory()
def synchrotron():
    """Create a Synchrotron instance with specific settings."""
    return Synchrotron()


@device_factory()
def waxs():
    """Create a WAXS detector with specific settings."""
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
        prefix="-EA-PILAT-03:",
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        metadata_holder=metadata_holder,
        path_provider=get_path_provider(),
    )


@device_factory()
def i0():
    """Create an I0 detector with specific settings."""
    return TetrammDetector(
        prefix="-EA-XBPM-02:",
        type="Cividec Diamond XBPM",
        path_provider=get_path_provider(),
    )


@device_factory()
def it():
    """Create an IT detector with specific settings."""
    return TetrammDetector(
        prefix="-EA-TTRM-02:",
        type="PIN Diode",
        path_provider=get_path_provider(),
    )


@device_factory()
def vfm():
    """Create a VFM instance with specific settings."""
    return FocusingMirror(name="vfm", prefix="-OP-KBM-01:VFM:")


@device_factory()
def hfm():
    """Create an HFM instance with specific settings."""
    return FocusingMirror(name="hfm", prefix="-OP-KBM-01:HFM:")


@device_factory()
def dcm():
    """Create a DCM instance with specific settings."""
    prefix = BeamlinePrefix(BL).beamline_prefix
    silicon_crystal_metadata = CrystalMetadata(
        usage="Bragg",
        type="silicon",
        reflection=(1, 1, 1),
        d_spacing=(3.13475, "nm"),
    )

    return DoubleCrystalMonochromator(
        motion_prefix=f"{prefix}-MO-DCM-01:",
        temperature_prefix=f"{prefix}-DI-DCM-01:",
        crystal_1_metadata=silicon_crystal_metadata,
        crystal_2_metadata=silicon_crystal_metadata,
    )


@device_factory()
def undulator():
    """Create an Undulator instance with specific settings."""
    return Undulator(
        prefix=f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        poles=80,
        length=2.0,
        id_gap_lookup_table_path="/dls_sw/i22/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
    )


@device_factory()
def slits_1():
    """Create Slits instance for slot 1."""
    return numbered_slits(1)


@device_factory()
def slits_2():
    """Create Slits instance for slot 2."""
    return numbered_slits(2)


@device_factory()
def slits_3():
    """Create Slits instance for slot 3."""
    return numbered_slits(3)


@device_factory()
def slits_4():
    """Create Slits instance for slot 4."""
    return numbered_slits(4)


@device_factory()
def slits_5():
    """Create Slits instance for slot 5."""
    return numbered_slits(5)


@device_factory()
def slits_6():
    """Create Slits instance for slot 6."""
    return numbered_slits(6)


@device_factory()
def fswitch():
    """Create an FSwitch instance with specific settings."""
    return FSwitch(
        prefix="-MO-FSWT-01:",
        lens_geometry="paraboloid",
        cylindrical=True,
        lens_material="Beryllium",
    )


@device_factory()
def panda1():
    """Create HDFPanda instance for panda1."""
    return HDFPanda(
        prefix="-EA-PANDA-01:",
        directory_provider=get_directory_provider(),
    )


@device_factory(skip=True)
def panda2():
    """Create HDFPanda instance for panda2."""
    return HDFPanda(
        prefix="-EA-PANDA-02:",
        directory_provider=get_directory_provider(),
    )


@device_factory(skip=True)
def panda3():
    """Create HDFPanda instance for panda3."""
    return HDFPanda(
        prefix="-EA-PANDA-03:",
        directory_provider=get_directory_provider(),
    )


@device_factory(skip=True)
def panda4():
    """Create HDFPanda instance for panda4."""
    return HDFPanda(
        prefix="-EA-PANDA-04:",
        directory_provider=get_directory_provider(),
    )


@device_factory()
def oav():
    """Create OAV instance with specific settings."""
    metadata_holder = NXSasMetadataHolder(
        x_pixel_size=(3.45e-3, "mm"),  # Double check this figure
        y_pixel_size=(3.45e-3, "mm"),
        description="AVT Mako G-507B",
        distance=(-1.0, "m"),
    )

    return NXSasOAV(
        prefix="-DI-OAV-01:",
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        metadata_holder=metadata_holder,
        directory_provider=get_directory_provider(),
    )


@device_factory()
def linkam():
    """Create Linkam3 instance with specific settings."""
    return Linkam3(prefix="-EA-TEMPC-05")
