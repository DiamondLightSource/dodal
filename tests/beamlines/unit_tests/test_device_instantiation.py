from typing import Any

import pytest

from dodal.beamlines import beamline_utils
from dodal.utils import BLUESKY_PROTOCOLS, make_all_devices

ALL_BEAMLINES = {"i03", "i04", "i04_1", "i20_1", "i22", "i23", "i24", "p38", "p45"}


def follows_bluesky_protocols(obj: Any) -> bool:
    return any((isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS))


@pytest.mark.parametrize(
    "module_and_devices_for_beamline", ALL_BEAMLINES, indirect=True
)
def test_device_creation(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    module, devices = module_and_devices_for_beamline
    for device_name, device in devices.items():
        assert device_name in beamline_utils.ACTIVE_DEVICES, (
            f"No device named {device_name} was created, devices "
            f"are {beamline_utils.ACTIVE_DEVICES.keys()}"
        )
        assert follows_bluesky_protocols(device)
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)


@pytest.mark.parametrize(
    "module_and_devices_for_beamline", ALL_BEAMLINES, indirect=True
)
def test_devices_are_identical(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device functions prevent duplicate instantiation.
    """
    bl_mod, devices_a = module_and_devices_for_beamline
    devices_b = make_all_devices(bl_mod, include_skipped=True, fake_with_ophyd_sim=True)
    for device_name in devices_a.keys():
        assert devices_a[device_name] is devices_b[device_name]
