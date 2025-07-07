from pathlib import Path

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.cryostream import OxfordCryoStream
from dodal.devices.i11.detectors import Mythen3
from dodal.devices.i11.diff_stages import DiffractometerBase, DiffractometerStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i11")
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
        Path(f"/dls/{BL}/data/2025/cm40625-3/bluesky"),
        client=RemoteDirectoryServiceClient(f"http://{BL}-control:8088/api"),
    )
)


@device_factory()
def mythen3() -> Mythen3:
    """i11 Oxford Cryostream 700 plus without cryoshutter"""
    return Mythen3(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-07:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix="HDF:",
    )


@device_factory()
def cstrm1() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 plus without cryoshutter"""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-01:")


@device_factory()
def cstrm2() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 standard without cryoshutter"""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-02:")


@device_factory()
def diffractometer_stage() -> DiffractometerStage:
    """Stage that contains the rotation axes, theta, two_theta, delta, spos"""
    return DiffractometerStage(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:")


@device_factory()
def diffractometer_base() -> DiffractometerBase:
    return DiffractometerBase(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:")


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
