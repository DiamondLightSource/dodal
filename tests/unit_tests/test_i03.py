import pytest
from ophyd import Device
from ophyd.sim import FakeEpicsSignal

from dodal import i03
from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.smargon import Smargon
from dodal.devices.zebra import Zebra


@pytest.fixture
def i03_devices():
    return i03.DEVICE_FUNCTIONS


@pytest.fixture
def i03_device_names():
    return i03.DEVICE_NAMES


def test_instantiate_function_makes_supplied_device():
    device_types = [Zebra, ApertureScatterguard, Smargon]
    for device in device_types:
        i03.clear_devices()
        dev = i03.device_instantiation(device, "device", "", False, False, None)
        assert isinstance(dev, device)


def test_instantiating_different_device_with_same_name():
    dev1 = i03.device_instantiation(Zebra, "device", "", False, False, None)  # noqa
    with pytest.raises(TypeError):
        dev2 = i03.device_instantiation(  # noqa
            Smargon, "device", "", False, False, None
        )
    i03.clear_device("device")
    dev2 = i03.device_instantiation(Smargon, "device", "", False, False, None)  # noqa


def test_instantiate_function_fake_makes_fake():
    fake_zeb: Zebra = i03.device_instantiation(i03.Zebra, "zebra", "", True, True, None)
    assert isinstance(fake_zeb, Device)
    assert isinstance(fake_zeb.pc.arm_source, FakeEpicsSignal)


def test_list():
    i03.zebra(wait_for_connection=False)
    i03.synchrotron(wait_for_connection=False)
    i03.aperture_scatterguard(wait_for_connection=False)
    assert i03.list_active_devices() == [
        "zebra",
        "synchrotron",
        "aperture_scatterguard",
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
