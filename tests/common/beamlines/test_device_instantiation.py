from typing import Any

import pytest
from ophyd_async.core import NotConnectedError

from dodal.beamlines import all_beamline_modules
from dodal.utils import BLUESKY_PROTOCOLS


def follows_bluesky_protocols(obj: Any) -> bool:
    return any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
# Increase timeout for this specific test as running individually can take over a second
# to import everything so causes tests to fail.
@pytest.mark.timeout(2)
def test_device_creation(module_and_devices_for_beamline):
    """Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    _, devices, exceptions = module_and_devices_for_beamline
    if len(exceptions) > 0:
        raise NotConnectedError(exceptions)
    devices_not_following_bluesky_protocols = [
        name
        for name, device in devices.items()
        if not follows_bluesky_protocols(device)
    ]
    assert len(devices_not_following_bluesky_protocols) == 0, (
        f"{devices_not_following_bluesky_protocols} do not follow bluesky protocols"
    )
