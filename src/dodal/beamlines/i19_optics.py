from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.device_manager import DeviceManager
from dodal.devices.attenuator.filter import FilterWheel
from dodal.devices.attenuator.filter_selections import I19FilterOneSelections
from dodal.devices.beamlines.i19.access_controlled.hutch_access import (
    ACCESS_DEVICE_NAME,
    HutchAccessControl,
)
from dodal.devices.focusing_mirror import FocusingMirrorWithPiezo
from dodal.devices.hutch_shutter import HutchShutter
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "i19-optics"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def access_control() -> HutchAccessControl:
    """Device to check which hutch is the active hutch on i19."""
    return HutchAccessControl(
        f"{PREFIX.beamline_prefix}-OP-STAT-01:", ACCESS_DEVICE_NAME
    )


@devices.factory()
def attenuator_x_motor() -> Motor:
    """Attenuator x motor - drives the resin wedge horizontally orthogonal to the x-ray beam.
    :return: Device for the attenuator system resin wedge horizontal motion.
    """
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-04:X", "ATTENUATOR_X")


@devices.factory()
def attenuator_y_motor() -> Motor:
    """Attenuator y motor - drives the aluminium / aluminum wedge vertically orthogonal to the x-ray beam.
    :return: Device for the attenuator system aluminium wedge vertical motion.
    """
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-05:Y", "ATTENUATOR_Y")


@devices.factory()
def filter_wheel() -> FilterWheel:
    """Filter wheel motor - rotates indexed wheel position to filters into/out of x-ray beam.
    :return: Device for the indexed filter wheel rotation.
    """
    return FilterWheel(
        f"{PREFIX.beamline_prefix}-MO-FILT-01:FILTER",
        I19FilterOneSelections,
        "FILTER_W",
    )


@devices.factory()
def hfm() -> FocusingMirrorWithPiezo:
    """Get the i19 hfm device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return FocusingMirrorWithPiezo(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@devices.factory()
def shutter() -> HutchShutter:
    """Real experiment shutter device for I19."""
    return HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")


@devices.factory()
def vfm() -> FocusingMirrorWithPiezo:
    """Get the i19 vfm device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return FocusingMirrorWithPiezo(f"{PREFIX.beamline_prefix}-OP-VFM-01:")
