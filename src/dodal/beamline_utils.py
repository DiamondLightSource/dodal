from typing import Callable, Dict, List, Optional

from ophyd import Device
from ophyd.sim import make_fake_device

from dodal.log import set_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

BL = get_beamline_name("s03")
set_beamline(BL)


ACTIVE_DEVICES: Dict[str, Device] = {}


def clear_devices():
    global ACTIVE_DEVICES
    for d in list(ACTIVE_DEVICES):
        del ACTIVE_DEVICES[d]


def clear_device(name: str):
    global ACTIVE_DEVICES
    del ACTIVE_DEVICES[name]


def list_active_devices() -> List[str]:
    global ACTIVE_DEVICES
    return list(ACTIVE_DEVICES.keys())


def active_device_is_same_type(active_device, device):
    return type(active_device) == device


@skip_device()
def device_instantiation(
    device: Callable,
    name: str,
    prefix: str,
    wait: bool,
    fake: bool,
    post_create: Optional[Callable] = None,
    bl_prefix: bool = True,
    **kwargs,
) -> Device:
    """Method to allow generic creation of singleton devices. Meant to be used to easily
    define lists of devices in beamline files. Additional keyword arguments are passed
    directly to the device constructor.

    Arguments:
        device: Callable        the device class
        name: str               the name for ophyd
        prefix: str             the PV prefix for the most (usually all) components
        wait: bool              whether to run .wait_for_connection()
        fake: bool              whether to fake with ophyd.sim
        post_create: Callable   (optional) a function to be run on the device after
                                creation
        bl_prefix: bool         if true, add the beamline prefix when instantiating, if
                                false the complete PV prefix must be supplied.
    Returns:
        The instance of the device.
    """
    active_device = ACTIVE_DEVICES.get(name)
    if fake:
        device = make_fake_device(device)
    if active_device is None:
        ACTIVE_DEVICES[name] = device(
            name=name,
            prefix=f"{(BeamlinePrefix(BL).beamline_prefix)}{prefix}"
            if bl_prefix
            else prefix,
            **kwargs,
        )
        if wait:
            ACTIVE_DEVICES[name].wait_for_connection()
    else:
        if not active_device_is_same_type(active_device, device):
            raise TypeError(
                f"Can't instantiate device of type {type(active_device)} with the same "
                f"name as an existing device. Device name '{name}' already used for "
                f"a(n) {device}."
            )
    if post_create:
        post_create(ACTIVE_DEVICES[name])
    return ACTIVE_DEVICES[name]
