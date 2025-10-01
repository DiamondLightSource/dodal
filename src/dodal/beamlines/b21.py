from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.eiger import EigerDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.devices.focusing_mirror import SimpleMirror
from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasOAV
from dodal.devices.linkam3 import Linkam3
from dodal.devices.motors import XYStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.v2f import QDV2F
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b21")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def saxs() -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-01:",
        hdf_suffix="-EA-EIGER-01:OD:",
        odin_nodes=1,
    )


@device_factory()
def waxs() -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-02:",
        hdf_suffix="-EA-EIGER-02:OD:",
        odin_nodes=1,
    )


@device_factory()
def mirror() -> SimpleMirror:
    return SimpleMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-MR-01:",
    )


@device_factory()
def it() -> QDV2F:
    return QDV2F(prefix=f"{PREFIX.beamline_prefix}-DI-PHDGN-07:PHD1:", I_suffix="I")


@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def table() -> XYStage:
    return XYStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-TABLE-04:",
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def slits_1() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


@device_factory()
def slits_2() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:")


@device_factory()
def slits_3() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:")


"""
Slits 4 was removed from B21 after the camera length was fixed, it is not used anymore.
"""


@device_factory()
def slits_5() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:")


@device_factory()
def slits_6() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:")


@device_factory()
def slits_7() -> Slits:
    """
    Compact JJ slits device is used for B21 slits 7. PV's operate in same way
    but physically different to other slits, and uses X:GAP nomenclature.
    """
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-07:",
        x_gap="X:GAP",
        y_gap="Y:GAP",
    )


@device_factory()
def wbscam() -> AravisDetector:
    metadata_holder = NXSasMetadataHolder(
        x_pixel_size=(1292, "pixels"),  # Double check this figure
        y_pixel_size=(964, "pixels"),
        description="Manta_G-125B",
        distance=(-1.0, "m"),
    )
    return NXSasOAV(
        prefix=f"{PREFIX.beamline_prefix}-RS-ABSB-02:CAM:",
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        path_provider=get_path_provider(),
        metadata_holder=metadata_holder,
    )


@device_factory(skip=True)
def linkam() -> Linkam3:
    return Linkam3(prefix=f"{PREFIX.beamline_prefix}-EA-HPLC-01:")


# TODO: https://github.com/DiamondLightSource/dodal/issues/1286
# def dmm() -> DMM: #b21 uses a dmm so
#     return DMM()
