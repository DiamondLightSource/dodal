from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.backlight import Backlight
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector
from dodal.devices.oav.oav_detector import OAV, OAVConfigParams
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

ZOOM_PARAMS_FILE = "/dls_sw/i04-1/software/gda/config/xml/jCameraManZoomLevels.xml"
DISPLAY_CONFIG = "/dls_sw/i04-1/software/gda_versions/var/display.configuration"

_simulator_beamline_fallback = "s04_1"
BL = get_beamline_name(_simulator_beamline_fallback)
set_log_beamline(BL)
set_utils_beamline(BL)


def _check_for_simulation():
    return BL == _simulator_beamline_fallback


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Backlight:
    """Get the i04_1 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
    """
    return device_instantiation(
        device_factory=Backlight,
        name="backlight",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(_check_for_simulation)
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: DetectorParams | None = None,
) -> EigerDetector:
    """Get the i04_1 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
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


@skip_device(_check_for_simulation)
def oav(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> OAV:
    """Get the i04_1 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        params=OAVConfigParams(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


def s4_slit_gaps(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> S4SlitGaps:
    """Get the i04_1 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
    """
    return device_instantiation(
        S4SlitGaps,
        "s4_slit_gaps",
        "-AL-SLITS-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(_check_for_simulation)
def synchrotron(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Synchrotron:
    """Get the i04_1 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
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
    """Get the i04_1 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
    """
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the i04_1 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04_1, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
