from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX
from dodal.devices.cryostream import OxfordCryoStream
from dodal.devices.eurotherm import (
    EurothermGeneral,
    UpdatingEurothermGeneral,
)
from dodal.devices.i11.cyberstar_blower import (
    AutotunedCyberstarBlower,
    CyberstarBlower,
)
from dodal.devices.i11.diff_stages import (
    DiffractometerBase,
    DiffractometerStage,
)
from dodal.devices.i11.mythen import Mythen3
from dodal.devices.i11.nx100robot import NX100Robot
from dodal.devices.i11.spinner import Spinner
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i11")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def mythen3() -> Mythen3:
    """Mythen3 Detector from PSI"""
    return Mythen3(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-07:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix="HDF:",
    )


@device_factory()
def ocs1() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 plus without cryoshutter"""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-01:")


@device_factory()
def ocs2() -> OxfordCryoStream:
    """i11 Oxford Cryostream 700 standard without cryoshutter"""
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-CG-CSTRM-02:")


@device_factory()
def diff_stage() -> DiffractometerStage:
    """Stage that contains the rotation axes, theta, two_theta, delta, spos"""
    return DiffractometerStage(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:")


@device_factory()
def diff_base() -> DiffractometerBase:
    return DiffractometerBase(prefix=f"{PREFIX.beamline_prefix}-MO-DIFF-01:BASE:")


@device_factory()
def csb1() -> CyberstarBlower[UpdatingEurothermGeneral]:
    """Cyberstar hot air blower 1 with Eurotherm Controller and updating PID"""
    return CyberstarBlower(
        prefix=f"{PREFIX.beamline_prefix}-EA-BLOW-01:",
        controller_type=UpdatingEurothermGeneral,
    )


@device_factory()
def csb2() -> AutotunedCyberstarBlower[EurothermGeneral]:
    """Cyberstar hot air blower 2 with autotuneable Eurotherm Controller"""
    return AutotunedCyberstarBlower(
        prefix=f"{PREFIX.beamline_prefix}-EA-BLOW-02:LOOP1:",
        controller_type=EurothermGeneral,
    )


@device_factory()
def sample_robot() -> NX100Robot:
    """The sample robot arm and carosel on i11 that moves
    and loads samples on/off the spinner"""
    return NX100Robot(prefix=f"{PREFIX.beamline_prefix}-EA-ROBOT-01:")


@device_factory()
def spinner() -> Spinner:
    """Sample spinner for powder averaging"""
    return Spinner(prefix=f"{PREFIX.beamline_prefix}-EA-ENV-01:")


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
