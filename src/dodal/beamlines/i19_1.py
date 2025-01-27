from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

# NOTE All PVs for both hutches have the prefix BL19I
BL = get_beamline_name("i19-1")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


I19_1_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_PILATUS=1),
    sources=ZebraSources(),
)

ZOOM_PARAMS_FILE = (
    "/dls_sw/i19-1/software/gda_versions/gda/config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i19-1/software/daq_configuration/domain/display.configuration"


@device_factory(skip=True)
def oav() -> OAV:
    return OAV(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        name="oav",
        config=OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i19-1 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Zebra(
        I19_1_ZEBRA_MAPPING,
        "zebra",
        f"{PREFIX.beamline_prefix}-EA-ZEBRA-03:",
    )


@device_factory()
def shutter() -> HutchShutter:
    """Get the i19-1 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    # See https://github.com/DiamondLightSource/dodal/issues/1020
    return HutchShutter(
        f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        "shutter",
    )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i19-1 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Synchrotron(
        "",
        "synchrotron",
    )
