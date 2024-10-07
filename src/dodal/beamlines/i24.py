from pathlib import Path

from dodal.common.beamlines.beamline_utils import (
    BL,
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitPathProvider
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i24.aperture import Aperture
from dodal.devices.i24.beamstop import Beamstop
from dodal.devices.i24.dcm import DCM
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.i24.i24_detector_motion import DetectorMotion
from dodal.devices.i24.i24_vgonio import VGonio
from dodal.devices.i24.pmac import PMAC
from dodal.devices.oav.oav_async import OAV as OAV2
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfigParams
from dodal.devices.oav.oav_utils import OAVConfig
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/scratch/tests"),
        # client=RemoteDirectoryServiceClient("http://i22-control:8088/api"),
    )
)


ZOOM_PARAMS_FILE = (
    "/dls_sw/i24/software/gda_versions/gda_9_34/config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i24/software/gda_versions/var/display.configuration"

BL = get_beamline_name("s24")
set_log_beamline(BL)
set_utils_beamline(BL)


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


@skip_device(lambda: BL == "s24")
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
    """Get the i24 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        params=OAVConfigParams(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@skip_device(lambda: BL == "s24")
def new_oav(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> OAV2:
    return device_instantiation(
        OAV2,
        "oav2",
        "-DI-OAV-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        config=OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
        path_provider=get_path_provider(),
    )


@skip_device(lambda: BL == "s24")
def vgonio(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> VGonio:
    """Get the i24 vgonio device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return device_instantiation(
        VGonio,
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


@skip_device(lambda: BL == "s24")
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
