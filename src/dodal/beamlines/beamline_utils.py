from typing import Callable, Dict, List, Optional, TypeVar, cast

from ophyd import Device
from ophyd.v2.core import Device as OphydV2Device, wait_for_connection as v2_device_wait_for_connection
from ophyd.sim import make_fake_device

from dodal.utils import BeamlinePrefix, skip_device

from bluesky.run_engine import call_in_bluesky_event_loop
import asyncio


ACTIVE_DEVICES: Dict[str, Device | OphydV2Device] = {}
BL = ""


def set_beamline(beamline: str):
    global BL
    BL = beamline


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


T = TypeVar("T", bound=Device | OphydV2Device)


def _wait_for_connection(device: Device | OphydV2Device) -> None:
    match device:
        case Device():
            device.wait_for_connection()
        case OphydV2Device():
            call_in_bluesky_event_loop(asyncio.wait_for(v2_device_wait_for_connection(coros=device.connect()), timeout=30))
        case _:
            raise TypeError("Invalid type {} in _wait_for_connection".format(device.__class__.__name__))


@skip_device()
def device_instantiation(
    device: Callable[..., T],
    name: str,
    prefix: str,
    wait: bool,
    fake: bool,
    post_create: Optional[Callable[[T], None]] = None,
    bl_prefix: bool = True,
    **kwargs,
) -> T:
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
        device_instance: T = device(
            name=name,
            prefix=f"{(BeamlinePrefix(BL).beamline_prefix)}{prefix}"
            if bl_prefix
            else prefix,
            **kwargs,
        )
        ACTIVE_DEVICES[name] = device_instance
        if wait:
            _wait_for_connection(device_instance)

    else:
        if not active_device_is_same_type(active_device, device):
            raise TypeError(
                f"Can't instantiate device of type {type(active_device)} with the same "
                f"name as an existing device. Device name '{name}' already used for "
                f"a(n) {device}."
            )
        else:
            # We have manually checked types
            device_instance: T = cast(T, ACTIVE_DEVICES[name])
    if post_create:
        post_create(device_instance)
    return device_instance
