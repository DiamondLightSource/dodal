from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.attenuator import Attenuator
from dodal.devices.backlight import Backlight
from dodal.devices.beamstop import BeamStop
from dodal.devices.dcm import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.i04.transfocator import Transfocator
from dodal.devices.ipin import IPin
from dodal.devices.motors import XYZPositioner
from dodal.devices.oav.oav_detector import OAV, OAVConfigParams
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import Undulator
from dodal.devices.xbpm_feedback import XBPMFeedbackI04
from dodal.devices.zebra import Zebra
from dodal.devices.zebra_controlled_shutter import ZebraShutter
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

ZOOM_PARAMS_FILE = (
    "/dls_sw/i04/software/gda/configurations/i04-config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i04/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i04/software/daq_configuration"

BL = get_beamline_name("s04")
set_log_beamline(BL)
set_utils_beamline(BL)


def smargon(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Smargon:
    """Get the i04 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Smargon,
        "smargon",
        "-MO-SGON-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def gonio_positioner(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    """Get the i04 lower_gonio_stages device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XYZPositioner,
        "lower_gonio_stages",
        "-MO-GONIO-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def sample_delivery_system(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    """Get the i04 sample_delivery_system device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XYZPositioner,
        "sample_delivery_system",
        "-MO-SDE-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def ipin(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> IPin:
    """Get the i04 ipin device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        IPin,
        "ipin",
        "-EA-PIN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def beamstop(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> BeamStop:
    """Get the i04 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        BeamStop,
        "beamstop",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def sample_shutter(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ZebraShutter:
    """Get the i04 sample shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        ZebraShutter,
        "sample_shutter",
        "-EA-SHTR-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def attenuator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Attenuator:
    """Get the i04 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Attenuator,
        "attenuator",
        "-EA-ATTN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def transfocator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Transfocator:
    """Get the i04 transfocator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Transfocator,
        "transfocator",
        "-MO-FSWT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def xbpm_feedback(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XBPMFeedbackI04:
    """Get the i04 xbpm_feedback device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XBPMFeedbackI04,
        "xbpm_feedback",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def flux(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Flux:
    """Get the i04 flux device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Flux,
        "flux",
        "-MO-FLUX-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    """Get the i04 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        DCM,
        "dcm",
        "-MO-DCM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Backlight:
    """Get the i04 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Backlight,
        "backlight",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def aperture_scatterguard(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    aperture_positions: AperturePositions | None = None,
) -> ApertureScatterguard:
    """Get the i04 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i04, it will return the existing
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


@skip_device(lambda: BL == "s04")
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: DetectorParams | None = None,
) -> EigerDetector:
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
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        post_create=set_params,
    )


def zebra_fast_grid_scan(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ZebraFastGridScan:
    """Get the i04 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        device_factory=ZebraFastGridScan,
        name="zebra_fast_grid_scan",
        prefix="-MO-SGON-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def s4_slit_gaps(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> S4SlitGaps:
    """Get the i04 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        S4SlitGaps,
        "s4_slit_gaps",
        "-AL-SLITS-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def undulator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Undulator:
    """Get the i04 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


@skip_device(lambda: BL == "s04")
def synchrotron(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Synchrotron:
    """Get the i04 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Synchrotron,
        "synchrotron",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the i04 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s04")
def oav(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> OAV:
    """Get the i04 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        params=OAVConfigParams(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@skip_device(lambda: BL == "s04")
def detector_motion(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorMotion:
    """Get the i04 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        device_factory=DetectorMotion,
        name="detector_motion",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def thawer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Thawer:
    """Get the i04 thawer, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Thawer,
        "thawer",
        "-EA-THAW-01",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def robot(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> BartRobot:
    """Get the i04 robot device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        BartRobot,
        "robot",
        "-MO-ROBOT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
