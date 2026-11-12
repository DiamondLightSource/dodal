from collections.abc import Mapping
from typing import Any

from bluesky.plan_stubs import rd
from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator, plan
from ophyd_async.core import Device, walk_devices


@plan
def state(*devices: Device) -> MsgGenerator[Mapping[str, Any | None]]:
    """Read the state of all readable devices in a device tree.

    Recursively traverses the device tree, reading every child that implements
    Readable and collecting its readings into a dictionary keyed by device name.
    Non-readable devices are included with a value of None.

    Args:
        devices: The root devices to retrieve the state of.

    Returns:
        A mapping of device names to their readings, or None if the device
        is not readable.
    """
    states = {}
    for device in devices:
        for _, dev in walk_devices(device).items():
            val = None
            if isinstance(dev, Readable):
                val = yield from rd(dev)
            states[dev.name] = val

    return states
