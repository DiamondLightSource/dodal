from functools import cache
from pathlib import Path

from ophyd_async.core import AutoMaxIncrementingPathProvider, PathProvider

from dodal.common.beamlines.beamline_utils import BL
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I24FilterOneSelections,
    I24FilterTwoSelections,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i24.aperture import Aperture
from dodal.devices.i24.beam_center import DetectorBeamCenter
from dodal.devices.i24.beamstop import Beamstop
from dodal.devices.i24.commissioning_jungfrau import CommissioningJungfrau
from dodal.devices.i24.dcm import DCM
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.i24.focus_mirrors import FocusMirrorsMode
from dodal.devices.i24.pmac import PMAC
from dodal.devices.i24.vgonio import VerticalGoniometer
from dodal.devices.motors import YZStage
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

ZOOM_PARAMS_FILE = (
    "/dls_sw/i24/software/gda_versions/gda/config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i24/software/gda_versions/var/display.configuration"


BL = get_beamline_name("i24")
set_log_beamline(BL)
set_utils_beamline(BL)

I24_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_EIGER=1, TTL_JUNGFRAU=2, TTL_FAST_SHUTTER=4),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/tmp"),
        client=LocalDirectoryServiceClient(),
    )


@devices.factory()
def attenuator() -> EnumFilterAttenuator:
    return EnumFilterAttenuator(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        filter_selection=(I24FilterOneSelections, I24FilterTwoSelections),
    )


@devices.factory()
def aperture() -> Aperture:
    return Aperture(f"{PREFIX.beamline_prefix}-AL-APTR-01:")


@devices.factory()
def beamstop() -> Beamstop:
    return Beamstop(f"{PREFIX.beamline_prefix}-MO-BS-01:")


@devices.factory()
def backlight() -> DualBacklight:
    return DualBacklight(prefix=PREFIX.beamline_prefix)


@devices.factory()
def detector_motion() -> YZStage:
    return YZStage(prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:")


@devices.factory()
def dcm() -> DCM:
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-DI-DCM-01:",
        motion_prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
    )


@devices.factory()
def pmac() -> PMAC:
    return PMAC(PREFIX.beamline_prefix)


@devices.factory()
def oav() -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@devices.factory()
def vgonio() -> VerticalGoniometer:
    return VerticalGoniometer(f"{PREFIX.beamline_prefix}-MO-VGON-01:")


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I24_ZEBRA_MAPPING,
    )


@devices.factory()
def shutter() -> HutchShutter:
    return HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")


@devices.factory()
def focus_mirrors() -> FocusMirrorsMode:
    return FocusMirrorsMode(f"{PREFIX.beamline_prefix}-OP-MFM-01:")


@devices.factory()
def eiger_beam_center() -> DetectorBeamCenter:
    return DetectorBeamCenter(f"{PREFIX.beamline_prefix}-EA-EIGER-01:CAM:", "eiger_bc")


@devices.factory()
def commissioning_jungfrau(
    path_provider: PathProvider,
) -> CommissioningJungfrau:
    """Get the commissionning Jungfrau 9M device, which uses a temporary filewriter
    device in place of Odin while the detector is in commissioning."""
    return CommissioningJungfrau(
        f"{PREFIX.beamline_prefix}-EA-JFRAU-01:",
        f"{PREFIX.beamline_prefix}-JUNGFRAU-META:FD:",
        AutoMaxIncrementingPathProvider(path_provider),
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def sample_shutter() -> ZebraShutter:
    return ZebraShutter(
        f"{PREFIX.beamline_prefix}-EA-SHTR-01:",
    )
