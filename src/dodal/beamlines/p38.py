from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import (
    DET_SUFFIX,
    HDF5_SUFFIX,
    numbered_slits,
)
from dodal.common.crystal_metadata import (
    MaterialsEnum,
    make_crystal_metadata_from_material,
)
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.i22.dcm import DoubleCrystalMonochromator
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.linkam3 import Linkam3
from dodal.devices.pressure_jump_cell import PressureJumpCell
from dodal.devices.slits import Slits
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.devices.watsonmarlow323_pump import WatsonMarlow323Pump
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

BL = get_beamline_name("p38")
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


def d3(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "d3",
        "-DI-DCAM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        path_provider=get_path_provider(),
    )


# Disconnected
@skip_device()
def d11(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "d11",
        "-DI-DCAM-03:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        path_provider=get_path_provider(),
    )


def d12(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    return device_instantiation(
        AravisDetector,
        "d12",
        "-DI-DCAM-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        path_provider=get_path_provider(),
    )


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


#
# The following devices are created as fake by default since P38 has no optics,
# but having mock devices here means they will be reflected in downstream data
# processing, where they may be required.
#


def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        1,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_2(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        2,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_3(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        3,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_4(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        4,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_5(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        5,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def slits_6(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
) -> Slits:
    return numbered_slits(
        6,
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def fswitch(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
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


def vfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
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
    fake_with_ophyd_sim: bool = True,
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
    fake_with_ophyd_sim: bool = True,
) -> DoubleCrystalMonochromator:
    return device_instantiation(
        DoubleCrystalMonochromator,
        "dcm",
        f"{BeamlinePrefix(BL).beamline_prefix}-MO-DCM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        temperature_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-DCM-01:",
        crystal_1_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
        crystal_2_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
    )


def undulator(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = True,
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


# Must find which PandA IOC(s) are compatible
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


@skip_device()
def linkam(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Linkam3:
    return device_instantiation(
        Linkam3,
        "linkam",
        f"{BeamlinePrefix(BL).insertion_prefix}-EA-LINKM-02:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def ppump(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = True
) -> WatsonMarlow323Pump:
    """Peristaltic Pump"""
    return device_instantiation(
        WatsonMarlow323Pump,
        "ppump",
        "-EA-PUMP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def high_pressure_xray_cell(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PressureJumpCell:
    return device_instantiation(
        PressureJumpCell,
        "high_pressure_xray_cell",
        f"{BeamlinePrefix(BL).insertion_prefix}-EA",
        wait_for_connection,
        fake_with_ophyd_sim,
        cell_prefix="-HPXC-01:",
        adc_prefix="-ADC",
    )
