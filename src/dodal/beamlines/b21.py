from pathlib import Path  # noqa

# from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline

# from dodal.common.beamlines.device_helpers import CAM_SUFFIX, DET_SUFFIX, HDF5_SUFFIX
# from dodal.common.crystal_metadata import (
#     MaterialsEnum,
#     make_crystal_metadata_from_material,
# )


from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider

# from dodal.devices.b21.dcm import DMM
from ophyd_async.fastcs.eiger import EigerDetector
# from dodal.devices.bimorph_mirror import BimorphMirror
# from dodal.devices.focusing_mirror import FocusingMirror

from dodal.devices.linkam3 import Linkam3
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
# from dodal.devices.tetramm import TetrammDetector
# from dodal.devices.undulator import Undulator

from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b21")
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
        Path("/dls/b21/data/2025/cm40642-3/bluesky"),
        client=RemoteDirectoryServiceClient("http://b21-control:8088/api"),
    )
)


@device_factory()
def saxs() -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-01:",
        hdf_suffix="-EA-EIGER-01:OD:",
    )


@device_factory()
def waxs() -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-02:",
        hdf_suffix="-EA-EIGER-02:OD:",
    )


@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
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
def slits_7() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-07:")


@device_factory(skip=True)
def linkam() -> Linkam3:
    return Linkam3(prefix=f"{PREFIX.beamline_prefix}-EA-HPLC-01:")


# @device_factory()
# def dmm() -> DMM: #b21 uses a dmm so, should write a device for that
#     return DMM(
#         prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
#         temperature_prefix=f"{PREFIX.beamline_prefix}-DI-DCM-01:",
#         crystal_1_metadata=make_crystal_metadata_from_material(
#             MaterialsEnum.Si, (1, 1, 1)
#         ),
#         crystal_2_metadata=make_crystal_metadata_from_material(
#             MaterialsEnum.Si, (1, 1, 1)
#         ),
#     )
