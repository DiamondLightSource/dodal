from typing import Any

import pytest
from ophyd_async.core import NotConnected

from dodal.beamlines import all_beamline_modules
from dodal.utils import BLUESKY_PROTOCOLS, make_all_devices


def follows_bluesky_protocols(obj: Any) -> bool:
    return any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
def test_device_creation(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    _, devices, exceptions = module_and_devices_for_beamline
    if len(exceptions) > 0:
        raise NotConnected(exceptions)
    devices_not_following_bluesky_protocols = [
        name
        for name, device in devices.items()
        if not follows_bluesky_protocols(device)
    ]
    assert len(devices_not_following_bluesky_protocols) == 0, (
        f"{devices_not_following_bluesky_protocols} do not follow bluesky protocols"
    )


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
def test_devices_are_identical(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device functions prevent duplicate instantiation.
    """
    bl_mod, devices_a, _ = module_and_devices_for_beamline
    devices_b, _ = make_all_devices(
        bl_mod,
        include_skipped=True,
        fake_with_ophyd_sim=True,
    )
    non_identical_names = [
        device_name
        for device_name, device in devices_a.items()
        if device is not devices_b[device_name]
    ]
    total_number_of_devices = len(devices_a)
    non_identical_number_of_devies = len(devices_a)
    assert len(non_identical_names) == 0, (
        f"{non_identical_number_of_devies}/{total_number_of_devices} devices were not identical: {non_identical_names}"
    )
