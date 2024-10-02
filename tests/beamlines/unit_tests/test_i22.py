import pytest


@pytest.mark.parametrize(
    "module_and_devices_for_beamline_device_factory", ["i22"], indirect=True
)
def test_device_creation(RE, module_and_devices_for_beamline_device_factory):
    _, devices = module_and_devices_for_beamline_device_factory
    expected_keys = [
        # "saxs",
        "synchrotron",
        # "waxs",
        # "i0", # todo it is missing the driver for now
        # "it", # todo it is missing the driver for now
        # "dcm",
        # "undulator",
        "vfm",
        "hfm",
        # "fswitch",
        # "panda1",
        # "panda2",
        # "panda3",
        # "panda4",
        # "oav",
        # "linkam",
    ]
    assert all(key in devices for key in expected_keys)
    # assert isinstance(devices["saxs"], PilatusDetector)
