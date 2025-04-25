from pathlib import Path

from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, RollCrystal
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.KBMirror import KBMirror
from dodal.devices.i18.table import Table
from dodal.devices.i18.thor_labs_stage import ThorLabsStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i18")
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
        Path("/dls/i18/data/2024/cm37264-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def undulator() -> Undulator:
    return Undulator(f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


# See https://github.com/DiamondLightSource/dodal/issues/1180
@device_factory(skip=True)
def dcm() -> BaseDCM[RollCrystal, PitchAndRollCrystal]:
    # once spacing is added Si111 d-spacing is 3.135 angsterm , and Si311 is 1.637
    # calculations are in gda/config/lookupTables/Si111/eV_Deg_converter.xml
    return BaseDCM(
        prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        xtal_1=RollCrystal,
        xtal_2=PitchAndRollCrystal,
    )


@device_factory()
def slits_1() -> Slits:
    return Slits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )


# PandA IOC needs to be updated to support PVI
@device_factory(skip=True)
def panda1() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def i0() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-02:",
        path_provider=get_path_provider(),
        type="Cividec Diamond XBPM",
    )


@device_factory()
def it() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-01:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
# VFM uses different IOC than HFM https://github.com/DiamondLightSource/dodal/issues/1009
def vfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-VFM-01:")


@device_factory()
def hfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@device_factory()
def d7diode() -> Diode:
    return Diode(f"{PREFIX.beamline_prefix}-DI-PHDGN-07:")


@device_factory()
def main_table() -> Table:
    return Table(f"{PREFIX.beamline_prefix}-MO-TABLE-01:")


@device_factory()
def thor_labs_stage() -> ThorLabsStage:
    return ThorLabsStage(f"{PREFIX.beamline_prefix}-MO-TABLE-02:")
