from dodal.beamline_specific_utils.i19 import HutchState, endstation_has_control
from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.common.coordination import locked
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i19.beamstop import BeamStop
from dodal.devices.i19.hutch_access import HutchAccessControl
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

# NOTE All PVs for both hutches and the optics have the prefix BL19I
BL = get_beamline_name("i19_1")
PREFIX = BeamlinePrefix("i19", "I")
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


@device_factory()
def access_control() -> HutchAccessControl:
    """Get a device that checks the active hutch for i19, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return HutchAccessControl(f"{PREFIX.beamline_prefix}-OP-STAT-01:")


# Needs to wait until enum is fixed on the beamline
# See https://github.com/DiamondLightSource/dodal/issues/1150
@device_factory()
def beamstop() -> BeamStop:
    """Get the i19-1 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return BeamStop(prefix=f"{PREFIX.beamline_prefix}-RS-ABSB-01:")


@device_factory()
def oav() -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-01:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i19-1 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Zebra(
        mapping=I19_1_ZEBRA_MAPPING,
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-03:",
    )


@device_factory()
def shutter() -> HutchShutter:
    """Get the i19 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    This shutter is locked, and can only be operated by the end station that is
    currently active, according to the access_control device.
    """
    shutter = HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")
    return locked(shutter, endstation_has_control(access_control(), HutchState.EH1))


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i19-1 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Synchrotron()
