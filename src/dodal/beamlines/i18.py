from pathlib import Path

from ophyd_async.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
		device_instantiation,
		get_directory_provider,
		set_directory_provider,
		)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import numbered_slits
from dodal.common.visit import DirectoryServiceClient, StaticVisitDirectoryProvider
from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i18")
set_log_beamline(BL)
set_utils_beamline(BL)


# MO-DCM-01 instead of DCSM
# 
# MO table is ok
# 
# xpress3 
# undulator?
# 
# ionchamber prefixes
# 
# pinhole PVs?
# -AL-APTR-01:TEMP1
# 
# DCM motion prefix? tem,pereature prefix? creystal Germanium metadta?
# 
# 
# mirrors:
# - vfm
# - hfm
# -OP-KBM-01:VFM:X.VAL
# 
# for ophyd-async new
# 
# table again, t1 theta and d7bdiode
# 
# 
# diode is ok, there are A and B variants
# motors A and B
# camera not used
# 
# diode reading and also DRAIN

# Currently we must hard-code the visit, determining the visit at runtime requires
# infrastructure that is still WIP.
# Communication with GDA is also WIP so for now we determine an arbitrary scan number
# locally and write the commissioning directory. The scan number is not guaranteed to
# be unique and the data is at risk - this configuration is for testing only.
set_directory_provider(
	StaticVisitDirectoryProvider(
		BL,
		Path("/dls/i18/data/2024/cm37264-2/bluesky"),
		client=DirectoryServiceClient("http://i18-control:8088/api"),
	)
)


def synchrotron( wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Synchrotron:
    return device_instantiation(
	Synchrotron,
	"synchrotron",
	"",
	wait_for_connection,
	fake_with_ophyd_sim,
)


def undulator(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Undulator:
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        # add CURRGAPD
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        poles=80,
        length=2.0,
    )


def slits_1(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    return numbered_slits(
        1,
	# BL18I-AL-SLITS-01
        wait_for_connection,
        fake_with_ophyd_sim,
    )


# Must document what PandAs are physically connected to
# See: https://github.com/bluesky/ophyd-async/issues/284
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
        directory_provider=get_directory_provider(),
    )


def xspress3(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Xspress3:
    """
    16 channels Xspress3 detector
	-EA-XPS-02:CAM:MaxSizeX_RBV
      also ArraySize
      also :CONNECTED
    """

    return device_instantiation(
        Xspress3,
        # prefix="-EA-DET-03:",
        prefix="-EA-XPS-02:",
        name="Xspress3",
        num_channels=16,
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
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


def i0(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "i0",
        "-EA-XBPM-02:",
        # -DI-XBPM-02:DEV:Firmware
        wait_for_connection,
        fake_with_ophyd_sim,
        type="Cividec Diamond XBPM",
        directory_provider=get_directory_provider(),
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
        directory_provider=get_directory_provider(),
    )
