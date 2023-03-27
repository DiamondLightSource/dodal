import pytest

from dodal import i03


@pytest.fixture
def i03_devices():
    return [
        i03.aperture_scatterguard,
        i03.backlight,
        i03.dcm,
        i03.eiger,
        i03.fast_grid_scan,
        i03.oav,
        i03.s4_slit_gaps,
        i03.smargon,
        i03.synchrotron,
        i03.undulator,
        i03.zebra,
    ]


@pytest.fixture
def i03_device_names():
    return [
        "aperture_scatterguard",
        "backlight",
        "dcm",
        "eiger",
        "fast_grid_scan",
        "oav",
        "s4_slit_gaps",
        "smargon",
        "synchrotron",
        "undulator",
        "zebra",
    ]


def test_device_creation(i03_devices, i03_device_names):
    for device, name in zip(i03_devices, i03_device_names):
        device(wait_for_connection=False)
        assert name in i03.ACTIVE_DEVICES
    assert len(i03.ACTIVE_DEVICES) == len(i03_device_names)


def test_devices_are_identical(i03_devices):
    for device in i03_devices:
        a = device(wait_for_connection=False)
        b = device(wait_for_connection=False)
        assert a is b


def test_clear_devices(i03_devices):
    for device in i03_devices:
        device(wait_for_connection=False)
    assert len(i03.ACTIVE_DEVICES) == len(i03_devices)
    i03.clear_devices()
    assert i03.ACTIVE_DEVICES == {}


def test_device_is_new_after_clearing(i03_devices):
    ids_1 = []
    ids_2 = []
    for device in i03_devices:
        ids_1.append(id(device(wait_for_connection=False)))
    for device in i03_devices:
        ids_2.append(id(device(wait_for_connection=False)))
    assert ids_1 == ids_2
    i03.clear_devices()
    ids_3 = []
    for device in i03_devices:
        ids_3.append(id(device(wait_for_connection=False)))
    assert ids_1 != ids_3
