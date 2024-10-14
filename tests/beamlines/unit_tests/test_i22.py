import pytest


@pytest.mark.parametrize(
    "module_and_devices_for_beamline_device_factory", ["i22"], indirect=True
)
def test_device_creation(RE, module_and_devices_for_beamline_device_factory):
    _, devices = module_and_devices_for_beamline_device_factory
    expected_keys = [
        "synchrotron",
        "vfm",
        "hfm",
    ]
    assert all(key in devices for key in expected_keys)
