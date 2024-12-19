from dodal.common.beamlines.beamline_utils import BL, device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator.attenuator import ReadOnlyAttenuator
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i24.aperture import Aperture
from dodal.devices.i24.beam_center import DetectorBeamCenter
from dodal.devices.i24.beamstop import Beamstop
from dodal.devices.i24.dcm import DCM
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.i24.focus_mirrors import FocusMirrorsMode
from dodal.devices.i24.i24_detector_motion import DetectorMotion
from dodal.devices.i24.pilatus_metadata import PilatusMetadata
from dodal.devices.i24.pmac import PMAC
from dodal.devices.i24.vgonio import VerticalGoniometer
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

ZOOM_PARAMS_FILE = (
    "/dls_sw/i24/software/gda_versions/gda/config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i24/software/gda_versions/var/display.configuration"

BL = get_beamline_name("s24")
set_log_beamline(BL)
set_utils_beamline(BL)


def attenuator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> ReadOnlyAttenuator:
    """Get a read-only attenuator device for i24, instantiate it if it hasn't already
    been. If this is called when already instantiated in i24, it will return the
    existing object."""
    return device_instantiation(
        ReadOnlyAttenuator,
        "attenuator",
        "-OP-ATTN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def aperture(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Aperture:
    """Get the i24 aperture device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        Aperture, "aperture", "-AL-APTR-01:", wait_for_connection, fake_with_ophyd_sim
    )


def beamstop(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Beamstop:
    """Get the i24 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        Beamstop,
        "beamstop",
        "-MO-BS-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DualBacklight:
    """Get the i24 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        device_factory=DualBacklight,
        name="backlight",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def detector_motion(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorMotion:
    """Get the i24 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        device_factory=DetectorMotion,
        name="detector_motion",
        prefix="-EA-DET-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    """Get the i24 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        device_factory=DCM,
        name="dcm",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s24")
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: DetectorParams | None = None,
) -> EigerDetector:
    """Get the i24 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
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


def pmac(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> PMAC:
    """Get the i24 PMAC device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    # prefix not BL but ME14E
    return device_instantiation(
        PMAC,
        "pmac",
        "ME14E-MO-CHIP-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


@skip_device(lambda: BL == "s24")
def oav(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> OAV:
    return device_instantiation(
        OAV,
        "oav",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        config=OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


def vgonio(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> VerticalGoniometer:
    """Get the i24 vertical goniometer device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return device_instantiation(
        VerticalGoniometer,
        "vgonio",
        "-MO-VGON-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the i24 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def shutter(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> HutchShutter:
    """Get the i24 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return device_instantiation(
        HutchShutter,
        "shutter",
        "-PS-SHTR-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def focus_mirrors(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> FocusMirrorsMode:
    """Get the i24 focus mirror devise to find the beam size."""
    return device_instantiation(
        FocusMirrorsMode,
        "focus_mirrors",
        "-OP-MFM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def eiger_beam_center(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorBeamCenter:
    """A device for setting/reading the beamcenter from the eiger on i24."""
    return device_instantiation(
        DetectorBeamCenter,
        "eiger_bc",
        "-EA-EIGER-01:CAM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def pilatus_beam_center(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorBeamCenter:
    """A device for setting/reading the beamcenter from the pilatus on i24."""
    return device_instantiation(
        DetectorBeamCenter,
        "pilatus_bc",
        "-EA-PILAT-01:cam1:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def pilatus_metadata(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PilatusMetadata:
    """A small pilatus driver device for figuring out the filename template."""
    return device_instantiation(
        PilatusMetadata,
        "pilatus_meta",
        "-EA-PILAT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
