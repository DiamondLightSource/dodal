import pytest


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i-min"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    print(devices)
    f = devices["fswitch"]
    p = devices["panda1"]
    assert f is not None
    assert p is not None
