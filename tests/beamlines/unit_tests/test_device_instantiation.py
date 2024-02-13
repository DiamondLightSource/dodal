from typing import Any

from dodal.beamlines import beamline_utils, i03, i04, i04_1, i23, i24, p38, p45
from dodal.utils import BLUESKY_PROTOCOLS, make_all_devices

ALL_BEAMLINES = {i03, i04, i04_1, i23, i24, p38, p45}


def follows_bluesky_protocols(obj: Any) -> bool:
    return any((isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS))


def test_device_creation(RE):
    """
    Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    for beamline in ALL_BEAMLINES:
        devices = make_all_devices(beamline, fake_with_ophyd_sim=True)
        for device_name, device in devices.items():
            assert device_name in beamline_utils.ACTIVE_DEVICES
            assert follows_bluesky_protocols(device)
        assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)
        beamline_utils.clear_devices()


def test_devices_are_identical(RE):
    """
    Ensures that for every beamline all device functions prevent duplicate instantiation.
    """
    for beamline in ALL_BEAMLINES:
        devices_a = make_all_devices(beamline, fake_with_ophyd_sim=True)
        devices_b = make_all_devices(beamline, fake_with_ophyd_sim=True)
        for device_name in devices_a.keys():
            assert devices_a[device_name] is devices_b[device_name]
        beamline_utils.clear_devices()
