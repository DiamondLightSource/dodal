from ophyd_async.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_directory_provider,
    set_directory_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.udc_directory_provider import PandASubdirectoryProvider
from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.attenuator import Attenuator
from dodal.devices.backlight import Backlight
from dodal.devices.dcm import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import PandAFastGridScan, ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, VFMMirrorVoltages
from dodal.devices.oav.oav_detector import OAV, OAVConfigParams
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.qbpm1 import QBPM1
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import Undulator
from dodal.devices.undulator_dcm import UndulatorDCM
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.xspress3_mini.xspress3_mini import Xspress3Mini
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

set_directory_provider(PandASubdirectoryProvider())


def aperture_scatterguard(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    aperture_positions: AperturePositions | None = None,
) -> ApertureScatterguard:
    """Get the i03 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i03, it will return the existing
    object. If aperture_positions is specified, it will update them.
    """

    def load_positions(a_s: ApertureScatterguard):
        if aperture_positions is not None:
            a_s.load_aperture_positions(aperture_positions)

    return device_instantiation(
        device_factory=ApertureScatterguard,
        name="aperture_scatterguard",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        post_create=load_positions,
    )


def attenuator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Attenuator:
    """Get the i03 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Attenuator,
        "attenuator",
        "-EA-ATTN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
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
def qbpm1(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> QBPM1:
    return device_instantiation(
        device_factory=QBPM1,
        name="qbpm1",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
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
def vfm_mirror_voltages(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> VFMMirrorVoltages:
    return device_instantiation(
        device_factory=VFMMirrorVoltages,
        name="vfm_mirror_voltages",
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
        prefix="-MO-SGON-01:FGS:",
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
        prefix="-MO-SGON-01:PGS:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def oav(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: OAVConfigParams | None = None,
) -> OAV:
    """Get the i03 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        params=params or OAVConfigParams(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
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
        id_gap_lookup_table_path="/dls_sw/i03/software/daq_configuration/lookup/BeamLine_Undulator_toGap.txt",
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
) -> Xspress3Mini:
    """Get the i03 Xspress3Mini device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Xspress3Mini,
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
        directory_provider=get_directory_provider(),
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
