from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import (
    device_factory,
    device_instantiation,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    load_positions_from_beamline_parameters,
)
from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator
from dodal.devices.backlight import Backlight
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I04Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.i03.dcm import DCM
from dodal.devices.i04.constants import RedisConstants
from dodal.devices.i04.murko_results import MurkoResultsDevice
from dodal.devices.i04.transfocator import Transfocator
from dodal.devices.ipin import IPin
from dodal.devices.motors import XYZPositioner
from dodal.devices.mx_phase1.beamstop import Beamstop
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import Undulator
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.devices.zocalo import ZocaloResults
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

ZOOM_PARAMS_FILE = (
    "/dls_sw/i04/software/gda/configurations/i04-config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i04/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i04/software/daq_configuration"


BL = get_beamline_name("s04")
set_log_beamline(BL)
set_utils_beamline(BL)

I04_ZEBRA_MAPPING = ZebraMapping(
    outputs=(ZebraTTLOutputs(TTL_DETECTOR=1, TTL_FAST_SHUTTER=2, TTL_XSPRESS3=3)),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)


@device_factory()
def smargon() -> Smargon:
    """Get the i04 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Smargon(
        f"{PREFIX.beamline_prefix}-MO-SGON-01:",
        "smargon",
    )


@device_factory()
def gonio_positioner() -> XYZPositioner:
    """Get the i04 lower_gonio_stages device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return XYZPositioner(
        f"{PREFIX.beamline_prefix}-MO-GONIO-01:",
        "lower_gonio_stages",
    )


@device_factory()
def sample_delivery_system() -> XYZPositioner:
    """Get the i04 sample_delivery_system device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return XYZPositioner(
        f"{PREFIX.beamline_prefix}-MO-SDE-01:",
        "sample_delivery_system",
    )


@device_factory()
def ipin() -> IPin:
    """Get the i04 ipin device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return IPin(
        f"{PREFIX.beamline_prefix}-EA-PIN-01:",
        "ipin",
    )


@device_factory()
def beamstop() -> Beamstop:
    """Get the i04 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Beamstop(
        f"{PREFIX.beamline_prefix}-MO-BS-01:",
        beamline_parameters=get_beamline_parameters(),
    )


@device_factory()
def sample_shutter() -> ZebraShutter:
    """Get the i04 sample shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return ZebraShutter(
        f"{PREFIX.beamline_prefix}-EA-SHTR-01:",
        "sample_shutter",
    )


@device_factory()
def attenuator() -> BinaryFilterAttenuator:
    """Get the i04 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return BinaryFilterAttenuator(
        f"{PREFIX.beamline_prefix}-EA-ATTN-01:",
        "attenuator",
    )


@device_factory()
def transfocator() -> Transfocator:
    """Get the i04 transfocator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Transfocator(
        f"{PREFIX.beamline_prefix}-MO-FSWT-01:",
        "transfocator",
    )


@device_factory()
def xbpm_feedback() -> XBPMFeedback:
    """Get the i04 xbpm_feedback device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return XBPMFeedback(
        PREFIX.beamline_prefix,
        "xbpm_feedback",
    )


@device_factory()
def flux(mock: bool = False) -> Flux:
    """Get the i04 flux device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Flux,
        "flux",
        "-MO-FLUX-01:",
        wait=False,
        fake=mock,
    )


@device_factory()
def dcm() -> DCM:
    """Get the i04 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return DCM(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        "dcm",
    )


@device_factory()
def backlight() -> Backlight:
    """Get the i04 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Backlight(
        PREFIX.beamline_prefix,
        "backlight",
    )


@device_factory()
def aperture_scatterguard() -> ApertureScatterguard:
    """Get the i04 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i04, it will return the existing
    object.
    """
    params = get_beamline_parameters()
    return ApertureScatterguard(
        prefix=PREFIX.beamline_prefix,
        name="aperture_scatterguard",
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


@device_factory(skip=BL == "s04")
def eiger(mock: bool = False, params: DetectorParams | None = None) -> EigerDetector:
    """Get the i04 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    If called with params, will update those params to the Eiger object.
    """

    def set_params(eiger: EigerDetector):
        if params is not None:
            eiger.set_detector_parameters(params)

    return device_instantiation(
        device_factory=EigerDetector,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=False,
        fake=mock,
        post_create=set_params,
    )


@device_factory()
def zebra_fast_grid_scan() -> ZebraFastGridScan:
    """Get the i04 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return ZebraFastGridScan(
        name="zebra_fast_grid_scan",
        prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:",
    )


@device_factory()
def s4_slit_gaps(mock: bool = False) -> S4SlitGaps:
    """Get the i04 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        S4SlitGaps,
        "s4_slit_gaps",
        "-AL-SLITS-04:",
        wait=False,
        fake=mock,
    )


@device_factory()
def undulator() -> Undulator:
    """Get the i04 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Undulator(
        name="undulator",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        id_gap_lookup_table_path="/dls_sw/i04/software/gda/config/lookupTables/BeamLine_Undulator_toGap.txt",
    )


@device_factory(skip=BL == "s04")
def synchrotron() -> Synchrotron:
    """Get the i04 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Synchrotron(
        "",
        "synchrotron",
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i04 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I04_ZEBRA_MAPPING,
    )


@device_factory(skip=BL == "s04")
def oav(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: OAVConfig | None = None,
) -> OAV:
    """Get the i04 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return OAV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        name="oav",
        config=params or OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory(skip=BL == "s04")
def detector_motion() -> DetectorMotion:
    """Get the i04 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return DetectorMotion(
        name="detector_motion",
        prefix=PREFIX.beamline_prefix,
    )


@device_factory()
def thawer() -> Thawer:
    """Get the i04 thawer, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return Thawer(
        f"{PREFIX.beamline_prefix}-EA-THAW-01",
        "thawer",
    )


@device_factory()
def robot() -> BartRobot:
    """Get the i04 robot device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return BartRobot(
        "robot",
        f"{PREFIX.beamline_prefix}-MO-ROBOT-01:",
    )


@device_factory()
def oav_to_redis_forwarder() -> OAVToRedisForwarder:
    """Get the i04 OAV to redis forwarder, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return OAVToRedisForwarder(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        name="oav_to_redis_forwarder",
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
    )


@device_factory()
def murko_results() -> MurkoResultsDevice:
    """Get the i04 OAV to redis forwarder, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return MurkoResultsDevice(
        name="murko_results",
        redis_host=RedisConstants.REDIS_HOST,
        redis_password=RedisConstants.REDIS_PASSWORD,
        redis_db=RedisConstants.MURKO_REDIS_DB,
    )


@device_factory()
def diamond_filter() -> DiamondFilter[I04Filters]:
    """Get the i04 diamond filter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return DiamondFilter[I04Filters](
        f"{PREFIX.beamline_prefix}-MO-FLTR-01:Y", I04Filters
    )


@device_factory()
def zocalo() -> ZocaloResults:
    """Get the i04 ZocaloResults device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return ZocaloResults(channel="xrc.i04")


@device_factory()
def pin_tip_detection() -> PinTipDetection:
    """Get the i04 pin tip detection device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return PinTipDetection(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
    )
