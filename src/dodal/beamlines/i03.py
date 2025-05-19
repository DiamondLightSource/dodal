from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import (
    device_factory,
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.udc_directory_provider import PandASubpathProvider
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    load_positions_from_beamline_parameters,
)
from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator
from dodal.devices.backlight import Backlight
from dodal.devices.baton import Baton
from dodal.devices.cryostream import CryoStream
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import PandAFastGridScan, ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, MirrorVoltages
from dodal.devices.i03 import Beamstop
from dodal.devices.i03.dcm import DCM
from dodal.devices.i03.undulator_dcm import UndulatorDCM
from dodal.devices.motors import XYZPositioner
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.qbpm import QBPM
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import Undulator
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.xspress3.xspress3 import Xspress3
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
    "/dls_sw/i03/software/gda/configurations/i03-config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i03/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i03/software/daq_configuration"

BL = get_beamline_name("i03")
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(PandASubpathProvider())

I03_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_SHUTTER=2, TTL_XSPRESS3=3, TTL_PANDA=4),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)


@device_factory()
def aperture_scatterguard() -> ApertureScatterguard:
    """Get the i03 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i03, it will return the existing
    object.
    """
    params = get_beamline_parameters()
    return ApertureScatterguard(
        prefix=PREFIX.beamline_prefix,
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


@device_factory()
def attenuator() -> BinaryFilterAttenuator:
    """Get the i03 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return BinaryFilterAttenuator(f"{PREFIX.beamline_prefix}-EA-ATTN-01:")


@device_factory()
def beamstop() -> Beamstop:
    """Get the i03 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Beamstop(
        prefix=f"{PREFIX.beamline_prefix}-MO-BS-01:",
        name="beamstop",
        beamline_parameters=get_beamline_parameters(),
    )


@device_factory()
def dcm() -> DCM:
    """Get the i03 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        name="dcm",
    )


@device_factory()
def vfm() -> FocusingMirrorWithStripes:
    return FocusingMirrorWithStripes(
        prefix=f"{PREFIX.beamline_prefix}-OP-VFM-01:",
        name="vfm",
        bragg_to_lat_lut_path=DAQ_CONFIGURATION_PATH
        + "/lookup/BeamLineEnergy_DCM_VFM_x_converter.txt",
        x_suffix="LAT",
        y_suffix="VERT",
    )


@device_factory()
def mirror_voltages() -> MirrorVoltages:
    return MirrorVoltages(
        name="mirror_voltages",
        prefix=f"{PREFIX.beamline_prefix}-MO-PSU-01:",
        daq_configuration_path=DAQ_CONFIGURATION_PATH,
    )


@device_factory()
def backlight() -> Backlight:
    """Get the i03 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Backlight(prefix=PREFIX.beamline_prefix, name="backlight")


@device_factory()
def detector_motion() -> DetectorMotion:
    """Get the i03 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return DetectorMotion(
        prefix=PREFIX.beamline_prefix,
        name="detector_motion",
    )


@device_factory()
def eiger(mock: bool = False) -> EigerDetector:
    """Get the i03 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """

    return device_instantiation(
        device_factory=EigerDetector,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=False,
        fake=mock,
    )


@device_factory()
def zebra_fast_grid_scan() -> ZebraFastGridScan:
    """Get the i03 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return ZebraFastGridScan(
        prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:",
        name="zebra_fast_grid_scan",
    )


@device_factory()
def panda_fast_grid_scan() -> PandAFastGridScan:
    """Get the i03 panda_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    This is used instead of the zebra_fast_grid_scan device when using the PandA.
    """
    return PandAFastGridScan(
        prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:",
        name="panda_fast_grid_scan",
    )


@device_factory()
def oav(
    params: OAVConfig | None = None,
) -> OAV:
    """Get the i03 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return OAV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        name="oav",
        config=params or OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def pin_tip_detection() -> PinTipDetection:
    """Get the i03 pin tip detection device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return PinTipDetection(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        "pin_tip_detection",
    )


@device_factory()
def smargon() -> Smargon:
    """Get the i03 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Smargon(f"{PREFIX.beamline_prefix}-MO-SGON-01:", "smargon")


@device_factory()
def s4_slit_gaps() -> S4SlitGaps:
    """Get the i03 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return S4SlitGaps(
        f"{PREFIX.beamline_prefix}-AL-SLITS-04:",
        "s4_slit_gaps",
    )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i03 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Synchrotron("", "synchrotron")


@device_factory()
def undulator(daq_configuration_path: str | None = None) -> Undulator:
    """Get the i03 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Undulator(
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        name="undulator",
        # evaluate here not as parameter default to enable post-import mocking
        id_gap_lookup_table_path=f"{daq_configuration_path or DAQ_CONFIGURATION_PATH}/lookup/BeamLine_Undulator_toGap.txt",
    )


@device_factory()
def undulator_dcm(daq_configuration_path: str | None = None) -> UndulatorDCM:
    """Get the i03 undulator DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    # evaluate here not as parameter default to enable post-import mocking
    undulator_singleton = (
        undulator(daq_configuration_path=daq_configuration_path)
        if daq_configuration_path and daq_configuration_path != DAQ_CONFIGURATION_PATH
        else undulator()
    )
    return UndulatorDCM(
        name="undulator_dcm",
        prefix=PREFIX.beamline_prefix,
        undulator=undulator_singleton,
        dcm=dcm(),
        daq_configuration_path=daq_configuration_path or DAQ_CONFIGURATION_PATH,
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i03 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I03_ZEBRA_MAPPING,
    )


@device_factory()
def xspress3mini() -> Xspress3:
    """Get the i03 Xspress3Mini device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Xspress3(
        f"{PREFIX.beamline_prefix}-EA-XSP3-01:",
        "xspress3mini",
    )


@device_factory()
def panda() -> HDFPanda:
    """Get the i03 panda device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
        name="panda",
    )


@device_factory()
def sample_shutter() -> ZebraShutter:
    """Get the i03 sample shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return ZebraShutter(
        f"{PREFIX.beamline_prefix}-EA-SHTR-01:",
        "sample_shutter",
    )


@device_factory()
def flux() -> Flux:
    """Get the i03 flux device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Flux(
        f"{PREFIX.beamline_prefix}-MO-FLUX-01:",
        "flux",
    )


@device_factory()
def xbpm_feedback() -> XBPMFeedback:
    """Get the i03 XBPM feeback device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return XBPMFeedback(
        PREFIX.beamline_prefix,
        "xbpm_feedback",
    )


@device_factory()
def zocalo() -> ZocaloResults:
    """Get the i03 ZocaloResults device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return ZocaloResults(
        name="zocalo",
        prefix=PREFIX.beamline_prefix,
    )


@device_factory()
def robot() -> BartRobot:
    """Get the i03 robot device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return BartRobot(
        "robot",
        f"{PREFIX.beamline_prefix}-MO-ROBOT-01:",
    )


@device_factory()
def webcam() -> Webcam:
    """Get the i03 webcam, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Webcam(
        "webcam",
        PREFIX.beamline_prefix,
        url="http://i03-webcam1/axis-cgi/jpg/image.cgi",
    )


@device_factory()
def thawer() -> Thawer:
    """Get the i03 thawer, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Thawer(
        f"{PREFIX.beamline_prefix}-EA-THAW-01",
        "thawer",
    )


@device_factory()
def lower_gonio() -> XYZPositioner:
    """Get the i03 lower gonio device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return XYZPositioner(
        f"{PREFIX.beamline_prefix}-MO-GONP-01:",
        "lower_gonio",
    )


@device_factory()
def cryo_stream() -> CryoStream:
    """Get the i03 cryostream device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return CryoStream(
        PREFIX.beamline_prefix,
        "cryo_stream",
    )


@device_factory()
def diamond_filter() -> DiamondFilter[I03Filters]:
    """Get the i03 diamond filter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return DiamondFilter[I03Filters](
        f"{PREFIX.beamline_prefix}-MO-FLTR-01:Y", I03Filters
    )


@device_factory()
def qbpm() -> QBPM:
    """Get the i03 qbpm device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return QBPM(
        f"{PREFIX.beamline_prefix}-DI-QBPM-01:",
        "qbpm",
    )


@device_factory(
    skip=True
)  # Skipping as not yet on the beamline, see https://jira.diamond.ac.uk/browse/I03-894
def baton() -> Baton:
    """Get the i03 baton device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Baton(f"{PREFIX.beamline_prefix}:")
