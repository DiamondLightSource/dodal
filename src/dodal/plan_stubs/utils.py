from collections.abc import Mapping
from typing import Any

from bluesky.plan_stubs import rd
from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator, plan
from ophyd_async.core import Device, walk_devices


@plan
def state(device: Device) -> MsgGenerator[Mapping[str, Any | None]]:
    """Read the state of all readable devices in a device tree.

    Recursively traverses the device tree, reading every child that implements
    Readable and collecting its readings into a dictionary keyed by device name.
    Non-readable devices are included with a value of None.

    Args:
        device: The root device to retrieve the state of.

    Returns:
        A mapping of device names to their readings, or None if the device
        is not readable.
    """
    device_state = {}
    tree = walk_devices(device)
    for _, dev in tree.items():
        val = None
        if isinstance(dev, Readable):
            val = yield from rd(dev)
        device_state[dev.name] = val

    return device_state
