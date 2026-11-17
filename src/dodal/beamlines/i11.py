from functools import cache
from pathlib import Path

from ophyd_async.core import (
    DeviceMap,
    PathProvider,
    StaticPathProvider,
    UUIDFilenameProvider,
)
from ophyd_async.epics.adcore import ADWriterFactory
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX
from dodal.common.enums import OpenCloseUpper
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i11.cyberstar_blower import (
    AutotunedCyberstarBlower,
    CyberstarBlower,
)
from dodal.devices.beamlines.i11.dcm import DCM
from dodal.devices.beamlines.i11.diff_stages import (
    DiffractometerBase,
    DiffractometerStage,
)
from dodal.devices.beamlines.i11.fastcs_mythen import FastCSMythen3
from dodal.devices.beamlines.i11.mythen import Mythen3
from dodal.devices.beamlines.i11.nx100robot import NX100Robot
from dodal.devices.beamlines.i11.simple_panda import SimplePanda
from dodal.devices.beamlines.i11.spinner import Spinner
from dodal.devices.cryostream import OxfordCryoStream
from dodal.devices.eurotherm import (
    EurothermGeneral,
    UpdatingEurothermGeneral,
)
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.scaler_card import ScalerCard, ScalerCardController
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperature_controller.mercury_itc import MercuryITC
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i11")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticPathProvider(UUIDFilenameProvider(), Path("/tmp"))


# Mythen detector state does not match ophyd-async see https://jira.diamond.ac.uk/browse/I11-916
@devices.factory(skip=True)
def mythen3(path_provider: PathProvider) -> Mythen3:
    """Mythen3 Detector from PSI."""
    return Mythen3(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-07:",
        writer_factory=ADWriterFactory.hdf(
            path_provider=path_provider, writer_suffix="HDF:"
        ),
        drv_suffix=DET_SUFFIX,
    )


@devices.factory()
def fastcs_mythen3(path_provider: PathProvider) -> FastCSMythen3:
    """FastCS Mythen3 Detector."""
    return FastCSMythen3(
        prefix=f"{PREFIX.beamline_prefix}-MYTHEN:",
        path_provider=path_provider,
    )


@devices.factory()
def ocs1() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 plus without cryoshutter."""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-01:")


@devices.factory()
def ocs2() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 standard without cryoshutter."""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-02:")


@devices.factory()
def diff_stage() -> DiffractometerStage:
    """Stage that contains the rotation axes, theta, two_theta, delta, spos."""
    return DiffractometerStage(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:")


@devices.factory()
def diff_base() -> DiffractometerBase:
    return DiffractometerBase(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:")


@devices.factory()
def csb1() -> CyberstarBlower[UpdatingEurothermGeneral]:
    """Cyberstar hot air blower 1 with Eurotherm Controller and updating PID."""
    return CyberstarBlower(
        prefix=f"{PREFIX.beamline_prefix}-EA-BLOW-01:",
        controller_type=UpdatingEurothermGeneral,
    )


@devices.factory()
def csb2() -> AutotunedCyberstarBlower[EurothermGeneral]:
    """Cyberstar hot air blower 2 with autotuneable Eurotherm Controller."""
    return AutotunedCyberstarBlower(
        prefix=f"{PREFIX.beamline_prefix}-EA-BLOW-02:LOOP1:",
        controller_type=EurothermGeneral,
    )


@devices.factory()
def sample_robot() -> NX100Robot:
    """The sample robot arm and carosel on i11 that moves
    and loads samples on/off the spinner.
    """
    return NX100Robot(prefix=f"{PREFIX.beamline_prefix}-EA-ROBOT-01:")


@devices.factory()
def spinner() -> Spinner:
    """Sample spinner for powder averaging."""
    return Spinner(prefix=f"{PREFIX.beamline_prefix}-EA-ENV-01:")


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def slits_1() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


@devices.factory()
def slits_2() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:")


@devices.factory()
def slits_3() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:")


@devices.factory()
def slits_4() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@devices.factory()
def slits_5() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:")


@devices.factory()
def dcm() -> DCM:
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        xtal_prefix=f"{PREFIX.beamline_prefix}-DI-DCM-01:",
    )


@devices.factory()
def panda(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def mercury_itc() -> MercuryITC:
    return MercuryITC(f"{PREFIX.beamline_prefix}-EA-MERC-01:")


@devices.factory()
def fast_shutter() -> FastShutter[OpenCloseUpper]:
    return FastShutter[OpenCloseUpper](
        f"{PREFIX.beamline_prefix}-EA-SHTR-01:SHUTTER",
        open_state=OpenCloseUpper.OPEN,
        close_state=OpenCloseUpper.CLOSE,
    )


@devices.factory()
def simple_panda() -> SimplePanda:
    return SimplePanda(f"{PREFIX.beamline_prefix}-EA-PANDA-01:")


@devices.factory()
def scaler2_controller() -> ScalerCardController:
    return ScalerCardController(
        f"{PREFIX.beamline_prefix}-EA-COUNT-02",
        start_count_suffix=".CNT",
        count_suffix=".TP",
    )


@devices.factory()
def scaler2(scaler2_controller: ScalerCardController) -> ScalerCard:
    prefix = f"{PREFIX.beamline_prefix}-EA-COUNT-02"
    return ScalerCard(
        channels=DeviceMap(
            {
                "i0": epics_signal_r(float, prefix + ".S17"),
                "ie": epics_signal_r(float, prefix + ".S18"),
            }
        ),
        controller=scaler2_controller,
    )
