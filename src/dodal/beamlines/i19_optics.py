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
from dodal.devices.hutch_shutter import InterlockedHutchShutter
from dodal.devices.interlocks import PSSInterlock
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "i19-optics"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def access_control() -> HutchAccessControl:
    """Device factory for access control device.

    I19 features two experimental hutches, EH-1 and EH-2,
    longitudinally positioned downstream from the common optics hutch:
    Only one active EH can control the optics.
    This device checks which EH is the active hutch.

    Uses:
        I19 beamline prefix extended with an infix specific to the access control.
        Name of the access device in i19-blueapi.
    """
    return HutchAccessControl(
        f"{PREFIX.beamline_prefix}-OP-STAT-01:", ACCESS_DEVICE_NAME
    )


@devices.factory()
def attenuator_x_motor() -> Motor:
    """Device factory for the I19 attenuator x-axis motor.

    The x-axis linear motor drives an absorber wedge horizontally orthogonal to the x-ray beam.

    Uses:
        Prefix for the I19 beamline extended with an infix specific to the attenuator x-axis motor.
        Name of the attenuator system x-axis motor device.

    Returns:
        Device for the x-axis attenuation system motor.
    """
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-04:X", "attenuator_x")


@devices.factory()
def attenuator_y_motor() -> Motor:
    """Device factory for the I19 attenuator y-axis motor.

    The y-axis linear motor drives an absorber wedge vertically orthogonal to the x-ray beam.

    Uses:
        Prefix for the I19 beamline extended with an infix specific to the attenuator y-axis motor.
        Name of the attenuator system y-axis motor device.

    Returns:
        Device for the y-axis attenuation system motor.
    """
    return Motor(f"{PREFIX.beamline_prefix}-OP-ATTN-05:Y", "attenuator_y")


@devices.factory()
def filter_wheel() -> FilterWheel:
    """Device factory for the I19 EH-1 filter wheel indexing motor.

    Filter wheel motor rotates indexed wheel to bring specific attenuating filter into/out of x-ray beam.

    Uses:
        Beamline prefix for I19 extended with infix specific to the filter motor.
        A further infix specific to filter wheel usage.
        Name of the first filter wheel.

    Returns:
        First indexed filter wheel slot selecting rotation device.
    """
    return FilterWheel(
        prefix=f"{PREFIX.beamline_prefix}-MO-FILT-01:",
        filter_infix="FILTER",
        filter_selections=I19FilterOneSelections,
        name="filter_w_1",
    )


@devices.factory()
def hfm() -> FocusingMirrorWithPiezo:
    """Device factory for the I19 Horizontal Focus Mirror (HFM) Piezo Device.

    Lazy instantiation:  Instantiates a device object if none have been,
    else it will return the pre-existing instance.

    Uses:
        I19 beamline prefix extended with an infix specific to the HFM.

    Returns:
         Focusing mirror piezo device for the HFM.
    """
    return FocusingMirrorWithPiezo(f"{PREFIX.beamline_prefix}-OP-HFM-01:")


@devices.factory()
def shutter() -> InterlockedHutchShutter:
    """Device factory for the I19 optics hutch shutter device.

    Uses:
        I19 beamline prefix extended with an infix specific to the optics hutch shutter.
        PSSInterlock device (itself using I19 beamline prefix)

    Returns:
        I19 optics hutch shutter device.
    """
    return InterlockedHutchShutter(
        PREFIX.beamline_prefix, PSSInterlock(PREFIX.beamline_prefix)
    )


@devices.factory()
def vfm() -> FocusingMirrorWithPiezo:
    """Device factory for the I19 Vertical Focus Mirror (VFM) Piezo Device.

    Lazy instantiation:  Instantiates a device object if none have been,
    else it will return the pre-existing instance.

    Uses:
        I19 beamline prefix with VFM infix.

    Returns:
         Focusing mirror piezo device for the VFM.
    """
    return FocusingMirrorWithPiezo(f"{PREFIX.beamline_prefix}-OP-VFM-01:")
