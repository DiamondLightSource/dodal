import pytest

from dodal.devices.synchrotron import Synchrotron


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i-min"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    print(devices)
    # ns = devices["numbered_slits"]
    s = devices["slits_6"]
    s = devices["fswitch"]
    p = devices["panda1"]
    assert s is not None
    assert isinstance(s, Synchrotron)
