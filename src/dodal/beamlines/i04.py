from ophyd_async.core import Reference

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    load_positions_from_beamline_parameters,
)
from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator
from dodal.devices.backlight import Backlight
from dodal.devices.baton import Baton
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I04Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import ZebraFastGridScanThreeD
from dodal.devices.flux import Flux
from dodal.devices.i03.dcm import DCM
from dodal.devices.i04.beam_centre import CentreEllipseMethod
from dodal.devices.i04.beamsize import Beamsize
from dodal.devices.i04.constants import RedisConstants
from dodal.devices.i04.max_pixel import MaxPixel
from dodal.devices.i04.murko_results import MurkoResultsDevice
from dodal.devices.i04.transfocator import Transfocator
from dodal.devices.ipin import IPin
from dodal.devices.motors import XYZStage
from dodal.devices.mx_phase1.beamstop import Beamstop
from dodal.devices.oav.oav_detector import (
    OAVBeamCentrePV,
)
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.scintillator import Scintillator
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import UndulatorInKeV
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.devices.zocalo import ZocaloResults
from dodal.devices.zocalo.zocalo_results import ZocaloSource
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

# Use BlueAPI scratch until https://github.com/DiamondLightSource/mx-bluesky/issues/1097 is done
ZOOM_PARAMS_FILE = "/dls_sw/i04/software/bluesky/scratch/jCameraManZoomLevels.xml"
DISPLAY_CONFIG = "/dls_sw/i04/software/bluesky/scratch/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i04/software/daq_configuration"


BL = get_beamline_name("i04")
set_log_beamline(BL)
set_utils_beamline(BL)

I04_ZEBRA_MAPPING = ZebraMapping(
    outputs=(ZebraTTLOutputs(TTL_DETECTOR=1, TTL_FAST_SHUTTER=2, TTL_XSPRESS3=3)),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)

devices = DeviceManager()


@devices.factory()
def smargon() -> Smargon:
    return Smargon(f"{PREFIX.beamline_prefix}-MO-SGON-01:")


@devices.factory()
def gonio_positioner() -> XYZStage:
    return XYZStage(
        f"{PREFIX.beamline_prefix}-MO-GONIO-01:",
        "lower_gonio_stages",
    )


@devices.factory()
def sample_delivery_system() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-SDE-01:")


@devices.factory()
def ipin() -> IPin:
    return IPin(f"{PREFIX.beamline_prefix}-EA-PIN-01:")


@devices.factory()
def beamstop() -> Beamstop:
    return Beamstop(
        f"{PREFIX.beamline_prefix}-MO-BS-01:",
        beamline_parameters=get_beamline_parameters(),
    )


@devices.factory()
def sample_shutter() -> ZebraShutter:
    return ZebraShutter(f"{PREFIX.beamline_prefix}-EA-SHTR-01:")


@devices.factory()
def attenuator() -> BinaryFilterAttenuator:
    return BinaryFilterAttenuator(
        prefix=f"{PREFIX.beamline_prefix}-EA-ATTN-01:",
        num_filters=16,
    )


@devices.factory()
def transfocator() -> Transfocator:
    return Transfocator(f"{PREFIX.beamline_prefix}-MO-FSWT-01:")


@devices.factory()
def baton() -> Baton:
    return Baton(f"{PREFIX.beamline_prefix}-CS-BATON-01:")


@devices.factory()
def xbpm_feedback(baton: Baton) -> XBPMFeedback:
    return XBPMFeedback(f"{PREFIX.beamline_prefix}-EA-FDBK-01:", baton=baton)


@devices.factory()
def flux() -> Flux:
    return Flux(f"{PREFIX.beamline_prefix}-MO-FLUX-01:")


@devices.factory()
def dcm() -> DCM:
    return DCM(f"{PREFIX.beamline_prefix}-MO-DCM-01:")


@devices.factory()
def backlight() -> Backlight:
    return Backlight(PREFIX.beamline_prefix)


@devices.factory()
def aperture_scatterguard() -> ApertureScatterguard:
    params = get_beamline_parameters()
    return ApertureScatterguard(
        aperture_prefix=f"{PREFIX.beamline_prefix}-MO-MAPT-01:",
        scatterguard_prefix=f"{PREFIX.beamline_prefix}-MO-SCAT-01:",
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


@devices.v1_init(EigerDetector, prefix="BL04I-EA-EIGER-01:", wait=False)
def eiger(eiger: EigerDetector) -> EigerDetector:
    eiger.detector_id = 78
    return eiger


@devices.factory()
def zebra_fast_grid_scan() -> ZebraFastGridScanThreeD:
    return ZebraFastGridScanThreeD(prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:")


@devices.factory()
def s4_slit_gaps() -> S4SlitGaps:
    return S4SlitGaps(f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@devices.fixture
def daq_configuration_path() -> str:
    return DAQ_CONFIGURATION_PATH


@devices.factory()
def undulator(baton: Baton, daq_configuration_path: str) -> UndulatorInKeV:
    return UndulatorInKeV(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        id_gap_lookup_table_path=f"{daq_configuration_path}/lookup/BeamLine_Undulator_toGap.txt",
        baton=baton,
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I04_ZEBRA_MAPPING,
    )


@devices.factory()
def oav(params: OAVConfig | None = None) -> OAVBeamCentrePV:
    return OAVBeamCentrePV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=params or OAVConfig(ZOOM_PARAMS_FILE),
    )


@devices.factory()
def oav_full_screen(params: OAVConfig | None = None) -> OAVBeamCentrePV:
    return OAVBeamCentrePV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=params or OAVConfig(ZOOM_PARAMS_FILE),
        overlay_channel=3,
        mjpeg_prefix="XTAL",
    )


@devices.factory()
def detector_motion() -> DetectorMotion:
    return DetectorMotion(
        device_prefix=f"{PREFIX.beamline_prefix}-MO-DET-01:",
        pmac_prefix=f"{PREFIX.beamline_prefix}-MO-PMAC-02:",
    )


@devices.factory()
def thawer() -> Thawer:
    return Thawer(f"{PREFIX.beamline_prefix}-EA-THAW-01")


@devices.factory()
def robot() -> BartRobot:
    return BartRobot(f"{PREFIX.beamline_prefix}-MO-ROBOT-01:")


@devices.factory()
def oav_to_redis_forwarder(
    oav: OAVBeamCentrePV, oav_full_screen: OAVBeamCentrePV
) -> OAVToRedisForwarder:
    return OAVToRedisForwarder(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        oav_roi=oav,
        oav_fs=oav_full_screen,
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
    )


@devices.factory()
def murko_results() -> MurkoResultsDevice:
    return MurkoResultsDevice(
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
    )


@devices.factory()
def diamond_filter() -> DiamondFilter[I04Filters]:
    return DiamondFilter[I04Filters](
        f"{PREFIX.beamline_prefix}-MO-FLTR-01:Y", I04Filters
    )


@devices.factory()
def zocalo() -> ZocaloResults:
    return ZocaloResults(channel="xrc.i04", results_source=ZocaloSource.CPU)


@devices.factory()
def pin_tip_detection() -> PinTipDetection:
    return PinTipDetection(f"{PREFIX.beamline_prefix}-DI-OAV-01:")


@devices.factory()
def scintillator(aperture_scatterguard: ApertureScatterguard) -> Scintillator:
    return Scintillator(
        f"{PREFIX.beamline_prefix}-MO-SCIN-01:",
        Reference(aperture_scatterguard),
        get_beamline_parameters(),
    )


@devices.factory()
def max_pixel() -> MaxPixel:
    return MaxPixel(f"{PREFIX.beamline_prefix}-DI-OAV-01:")


@devices.factory()
def beamsize(
    transfocator: Transfocator, aperture_scatterguard: ApertureScatterguard
) -> Beamsize:
    return Beamsize(
        transfocator,
        aperture_scatterguard,
    )


@devices.factory()
def beam_centre() -> CentreEllipseMethod:
    return CentreEllipseMethod(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
    )
