import pytest
from ophyd_async.epics.adpilatus import PilatusDetector


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i22"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    print(devices)
    expected_keys = [
        "saxs",
        "synchrotron",
        "waxs",
        # "i0", # todo it is missing the driver for now
        # "it", # todo it is missing the driver for now
        "dcm",
        "undulator",
        "vfm",
        "hfm",
        "fswitch",
        "panda1",
        "panda2",
        "panda3",
        "panda4",
        "oav",
        "linkam",
    ]
    for key in expected_keys:
        assert key in devices
        assert devices[key] is not None
    assert isinstance(devices["saxs"], PilatusDetector)
