from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i18.diode import Diode
from dodal.devices.beamlines.i18.kb_mirror import KBMirror
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    RollCrystal,
)
from dodal.devices.motors import XYStage, XYZThetaStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import UndulatorInKeV
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i18")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    # Currently we must hard-code the visit, determining the visit at runtime requires
    # infrastructure that is still WIP.
    # Communication with GDA is also WIP so for now we determine an arbitrary scan number
    # locally and write the commissioning directory. The scan number is not guaranteed to
    # be unique and the data is at risk - this configuration is for testing only.
    return StaticVisitPathProvider(
        BL,
        Path("/dls/i18/data/2024/cm37264-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def undulator() -> UndulatorInKeV:
    return UndulatorInKeV(f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


# See https://github.com/DiamondLightSource/dodal/issues/1180
@devices.factory(skip=True)
def dcm() -> DoubleCrystalMonochromatorWithDSpacing:
    """A double crystal monocromator device, used to select the beam energy.

    Once spacing is added Si111 d-spacing is 3.135 angsterm , and Si311 is 1.637
    calculations are in gda/config/lookupTables/Si111/eV_Deg_converter.xml
    """
    return DoubleCrystalMonochromatorWithDSpacing(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:", RollCrystal, PitchAndRollCrystal
    )


@devices.factory()
def slits_1() -> Slits:
    return Slits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


# PandA IOC needs to be updated to support PVI
@devices.factory(skip=True)
def panda1(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def i0(path_provider: PathProvider) -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-02:",
        path_provider=path_provider,
        type="Cividec Diamond XBPM",
    )


@devices.factory()
def it(path_provider: PathProvider) -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-01:",
        path_provider=path_provider,
    )


@devices.factory(skip=True)
# VFM uses different IOC than HFM https://github.com/DiamondLightSource/dodal/issues/1009
def vfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-VFM-01:")


@devices.factory()
def hfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@devices.factory()
def d7_diode() -> Diode:
    return Diode(f"{PREFIX.beamline_prefix}-DI-PHDGN-07:")


@devices.factory()
def main_table() -> XYZThetaStage:
    return XYZThetaStage(f"{PREFIX.beamline_prefix}-MO-TABLE-01:")


@devices.factory()
def thor_labs_stage() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-TABLE-02:")
