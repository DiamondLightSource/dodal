from ophyd_async.fastcs.panda import HDFPanda

from dodal.beamline_specific_utils.i19 import HutchState, endstation_has_control
from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.common.coordination import locked
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i19.backlight import BacklightPosition
from dodal.devices.i19.beamstop import BeamStop
from dodal.devices.i19.diffractometer import FourCircleDiffractometer
from dodal.devices.i19.hutch_access import HutchAccessControl
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
def access_control() -> HutchAccessControl:
    """Get a device that checks the active hutch for i19, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return HutchAccessControl(f"{PREFIX.beamline_prefix}-OP-STAT-01:")


@device_factory()
def diffractometer() -> FourCircleDiffractometer:
    return FourCircleDiffractometer(prefix=PREFIX.beamline_prefix)


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
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-03:",
    )


@device_factory()
def shutter() -> HutchShutter:
    """Get the i19 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    shutter = HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")
    return locked(shutter, endstation_has_control(access_control(), HutchState.EH2))


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i19-2 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-2, it will return the existing object.
    """
    return Synchrotron()


@device_factory()
def backlight() -> BacklightPosition:
    """Get the i19-2 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-2, it will return the existing object.
    """
    return BacklightPosition(prefix=f"{PREFIX.beamline_prefix}-EA-IOC-12:")


@device_factory()
def panda() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )
