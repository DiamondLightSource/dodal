from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.devices.i19.beamstop import BeamStop
from dodal.devices.i19.blueapi_device import HutchState
from dodal.devices.i19.shutter import AccessControlledShutter
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

# NOTE all workstations on I19 default to i19-1 as beamline name
# Unless variable is exported (which is not usually done by scientists)
# NOTE All PVs for both hutches and the optics have the prefix BL19I
BL = "i19-2"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)


I19_2_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(),
    sources=ZebraSources(),
)


@device_factory()
def beamstop() -> BeamStop:
    """Get the i19-2 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-2, it will return the existing object.
    """
    return BeamStop(prefix=f"{PREFIX.beamline_prefix}-OP-ABSB-02:")


@device_factory()
def zebra() -> Zebra:
    """Get the i19-2 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-2, it will return the existing object.
    """
    return Zebra(
        mapping=I19_2_ZEBRA_MAPPING,
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
    )


@device_factory()
def shutter() -> AccessControlledShutter:
    """Get the i19-2 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return AccessControlledShutter(
        prefix=f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        hutch=HutchState.EH2,
    )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i19-2 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-2, it will return the existing object.
    """
    return Synchrotron()
