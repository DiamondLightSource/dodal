from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import (
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
from dodal.devices.cryostream import CryoStream
from dodal.devices.dcm import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import PandAFastGridScan, ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, MirrorVoltages
from dodal.devices.i03.beamstop import Beamstop
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
from dodal.devices.undulator_dcm import UndulatorDCM
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.devices.zebra import Zebra
from dodal.devices.zebra_controlled_shutter import ZebraShutter
from dodal.devices.zocalo import ZocaloResults
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

ZOOM_PARAMS_FILE = (
    "/dls_sw/i03/software/gda/configurations/i03-config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i03/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i03/software/daq_configuration"

BL = get_beamline_name("s03")
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(PandASubpathProvider())


def aperture_scatterguard(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> ApertureScatterguard:
    """Get the i03 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i03, it will return the existing
    object.
    """
    params = get_beamline_parameters()
    return device_instantiation(
        device_factory=ApertureScatterguard,
        name="aperture_scatterguard",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


def attenuator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> BinaryFilterAttenuator:
    """Get the i03 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        BinaryFilterAttenuator,
        "attenuator",
        "-EA-ATTN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def beamstop(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Beamstop:
    """Get the i03 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Beamstop,
        "beamstop",
        "-MO-BS-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        beamline_parameters=get_beamline_parameters(),
    )


def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    """Get the i03 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        DCM,
        "dcm",
        "-MO-DCM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def vfm(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> FocusingMirrorWithStripes:
    return device_instantiation(
        device_factory=FocusingMirrorWithStripes,
        name="vfm",
        prefix="-OP-VFM-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bragg_to_lat_lut_path=DAQ_CONFIGURATION_PATH
        + "/lookup/BeamLineEnergy_DCM_VFM_x_converter.txt",
        x_suffix="LAT",
        y_suffix="VERT",
    )


@skip_device(lambda: BL == "s03")
def mirror_voltages(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> MirrorVoltages:
    return device_instantiation(
        device_factory=MirrorVoltages,
        name="mirror_voltages",
        prefix="-MO-PSU-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        daq_configuration_path=DAQ_CONFIGURATION_PATH,
    )


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Backlight:
    """Get the i03 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device_factory=Backlight,
        name="backlight",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def detector_motion(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorMotion:
    """Get the i03 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device_factory=DetectorMotion,
        name="detector_motion",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: DetectorParams | None = None,
) -> EigerDetector:
    """Get the i03 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    If called with params, will update those params to the Eiger object.
    """

    def set_params(eiger: EigerDetector):
        if params is not None:
            eiger.set_detector_parameters(params)

    return device_instantiation(
        device_factory=EigerDetector,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        post_create=set_params,
    )


def zebra_fast_grid_scan(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ZebraFastGridScan:
    """Get the i03 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device_factory=ZebraFastGridScan,
        name="zebra_fast_grid_scan",
        prefix="-MO-SGON-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def panda_fast_grid_scan(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PandAFastGridScan:
    """Get the i03 panda_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    This is used instead of the zebra_fast_grid_scan device when using the PandA.
    """
    return device_instantiation(
        device_factory=PandAFastGridScan,
        name="panda_fast_grid_scan",
        prefix="-MO-SGON-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def oav(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: OAVConfig | None = None,
) -> OAV:
    """Get the i03 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        config=params or OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@skip_device(lambda: BL == "s03")
def pin_tip_detection(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PinTipDetection:
    """Get the i03 pin tip detection device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        PinTipDetection,
        "pin_tip_detection",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def smargon(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Smargon:
    """Get the i03 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Smargon,
        "smargon",
        "-MO-SGON-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def s4_slit_gaps(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> S4SlitGaps:
    """Get the i03 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        S4SlitGaps,
        "s4_slit_gaps",
        "-AL-SLITS-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def synchrotron(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Synchrotron:
    """Get the i03 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Synchrotron,
        "synchrotron",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def undulator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Undulator:
    """Get the i03 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        id_gap_lookup_table_path="/dls_sw/i03/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
    )


def undulator_dcm(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorDCM:
    """Get the i03 undulator DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        UndulatorDCM,
        name="undulator_dcm",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        undulator=undulator(wait_for_connection, fake_with_ophyd_sim),
        dcm=dcm(wait_for_connection, fake_with_ophyd_sim),
        daq_configuration_path=DAQ_CONFIGURATION_PATH,
    )


def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the i03 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def xspress3mini(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Xspress3:
    """Get the i03 Xspress3Mini device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Xspress3,
        "xspress3mini",
        "-EA-XSP3-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def panda(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> HDFPanda:
    """Get the i03 panda device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        HDFPanda,
        "panda",
        "-EA-PANDA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        path_provider=get_path_provider(),
    )


@skip_device(lambda: BL == "s03")
def sample_shutter(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ZebraShutter:
    """Get the i03 sample shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        ZebraShutter,
        "sample_shutter",
        "-EA-SHTR-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def flux(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Flux:
    """Get the i03 flux device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Flux,
        "flux",
        "-MO-FLUX-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def xbpm_feedback(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XBPMFeedback:
    """Get the i03 XBPM feeback device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        XBPMFeedback,
        "xbpm_feedback",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def zocalo(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ZocaloResults:
    """Get the i03 ZocaloResults device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        ZocaloResults,
        "zocalo",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def robot(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> BartRobot:
    """Get the i03 robot device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        BartRobot,
        "robot",
        "-MO-ROBOT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def webcam(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Webcam:
    """Get the i03 webcam, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Webcam,
        "webcam",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        url="http://i03-webcam1/axis-cgi/jpg/image.cgi",
    )


def thawer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Thawer:
    """Get the i03 thawer, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Thawer,
        "thawer",
        "-EA-THAW-01",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def lower_gonio(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    """Get the i03 lower gonio device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        XYZPositioner,
        "lower_gonio",
        "-MO-GONP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def cryo_stream(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> CryoStream:
    """Get the i03 cryostream device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        CryoStream,
        "cryo_stream",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def diamond_filter(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DiamondFilter[I03Filters]:
    """Get the i03 diamond filter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        DiamondFilter[I03Filters],
        "diamond_filter",
        "-MO-FLTR-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        data_type=I03Filters,
    )


def qbpm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> QBPM:
    """Get the i03 qbpm device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        QBPM,
        "qbpm",
        "-DI-QBPM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
