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
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    RemoteDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasOAV, NXSasPilatus
from dodal.devices.linkam3 import Linkam3
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device
from dodal.cli import LAB_NAME, LAB_FLAG


BL = LAB_NAME if LAB_FLAG else get_beamline_name("i22")
print("BL NAME: ", BL)
set_log_beamline(BL)
set_utils_beamline(BL)

IS_LAB = LAB_FLAG and BL == LAB_NAME
print("is this lab? : ",IS_LAB)

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
    if IS_LAB
    else StaticVisitPathProvider(
        BL,
        Path("/dls/i22/data/2024/cm37271-2/bluesky"),
        client=RemoteDirectoryServiceClient("http://i22-control:8088/api"),
    )
)


# d11 at p38, but disconnected
def saxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector | NXSasPilatus:

    if IS_LAB:
        return device_instantiation(
            AravisDetector ,
            "d11",
            "-DI-DCAM-03:",
            wait_for_connection,
            fake_with_ophyd_sim,
            drv_suffix="DET:" ,
            hdf_suffix="HDF5:",
            # metadata_holder=NXSasMetadataHolder(
            #     x_pixel_size=(1.72e-1, "mm"),
            #     y_pixel_size=(1.72e-1, "mm"),
            #     description="Dectris Pilatus3 2M",
            #     type="Photon Counting Hybrid Pixel",
            #     sensor_material="silicon",
            #     sensor_thickness=(0.45, "mm"),
            #     distance=(4711.833684146172, "mm"),
            # ),
            directory_provider=get_directory_provider(),
        )

    return device_instantiation(
         NXSasPilatus,
         "saxs",
        "-EA-PILAT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        metadata_holder=NXSasMetadataHolder(
            x_pixel_size=(1.72e-1, "mm"),
            y_pixel_size=(1.72e-1, "mm"),
            description="Dectris Pilatus3 2M",
            type="Photon Counting Hybrid Pixel",
            sensor_material="silicon",
            sensor_thickness=(0.45, "mm"),
            distance=(4711.833684146172, "mm"),
        ),
        path_provider=get_path_provider(),
    )


@skip_device(lambda: BL == LAB_NAME)
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


# d12 at p38
def waxs(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PilatusDetector:
    return device_instantiation(
        AravisDetector if IS_LAB else NXSasPilatus,
        "d12" if IS_LAB else "waxs",
        "-DI-DCAM-04:" if IS_LAB else "-EA-PILAT-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:" if IS_LAB else "CAM:",
        hdf_suffix="HDF5:",
        metadata_holder=NXSasMetadataHolder(
            x_pixel_size=(1.72e-1, "mm"),
            y_pixel_size=(1.72e-1, "mm"),
            description="Dectris Pilatus3 2M",
            type="Photon Counting Hybrid Pixel",
            sensor_material="silicon",
            sensor_thickness=(0.45, "mm"),
            distance=(175.4199417092314, "mm"),
        ),
        path_provider=get_path_provider(),
    )


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        f"-EA-XBPM-0{1 if IS_LAB else 2}:",
        wait_for_connection,
        fake_with_ophyd_sim,
        type="Cividec Diamond XBPM",
        path_provider=get_path_provider(),
    )


def it(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "it",
        "-EA-TTRM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        type="PIN Diode",
        path_provider=get_path_provider(),
    )


def vfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "vfm",
        "-OP-KBM-01:VFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def hfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "hfm",
        "-OP-KBM-01:HFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


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
        crystal_1_metadata=CrystalMetadata(
            usage="Bragg",
            type="silicon",
            reflection=(1, 1, 1),
            d_spacing=(3.13475, "nm"),
        ),
        crystal_2_metadata=CrystalMetadata(
            usage="Bragg",
            type="silicon",
            reflection=(1, 1, 1),
            d_spacing=(3.13475, "nm"),
        ),
    )


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
        id_gap_lookup_table_path="/dls_sw/i22/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
    )


#
# The following devices are fake by default since P38 has no optics,
# but having mock devices here means they will be reflected in downstream data
# processing, where they may be required.
#


def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        1,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        2,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        3,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        4,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_5(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        5,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_6(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        6,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def fswitch(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FSwitch:
    return device_instantiation(
        FSwitch,
        "fswitch",
        "-MO-FSWT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        lens_geometry="paraboloid",
        cylindrical=True,
        lens_material="Beryllium",
    )


# Must find which PandA IOC(s) are compatible
# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
def panda1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda1",
        "-EA-PANDA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


@skip_device()
def panda2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda2",
        "-EA-PANDA-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


@skip_device()
def panda3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda3",
        "-EA-PANDA-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


@skip_device(lambda: BL == LAB_NAME)
def panda4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> HDFPanda:
    return device_instantiation(
        HDFPanda,
        "panda4",
        "-EA-PANDA-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


# d3 at p38
def oav(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector if IS_LAB else NXSasOAV,
        "d3" if IS_LAB else "oav",
        f"-DI-{'DCAM' if IS_LAB else 'OAV'}-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        metadata_holder=NXSasMetadataHolder(
            x_pixel_size=(3.45e-3, "mm"),  # Double check this figure
            y_pixel_size=(3.45e-3, "mm"),
            description="AVT Mako G-507B",
            distance=(-1.0, "m"),
        ),
        path_provider=get_path_provider(),
    )


@skip_device()
def linkam(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Linkam3:
    return device_instantiation(
        Linkam3,
        "linkam",
        "-EA-TEMPC-05" if IS_LAB else "-EA-TEMPC-05",
        # note alternatively -EA-LINKM-02:
        wait_for_connection,
        fake_with_ophyd_sim,
    )
