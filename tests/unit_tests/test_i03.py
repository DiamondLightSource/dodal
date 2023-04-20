import numpy as np
import pytest
from ophyd import Device
from ophyd.sim import FakeEpicsSignal

from dodal import i03
from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.smargon import Smargon
from dodal.devices.zebra import Zebra
from dodal.utils import create_point, make_all_devices


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


def test_device_creation():
    devices = make_all_devices(i03, fake_with_ophyd_sim=True)
    for device_name in devices.keys():
        assert device_name in i03.ACTIVE_DEVICES
    assert len(i03.ACTIVE_DEVICES) == len(devices)


def test_devices_are_identical():
    devices_a = make_all_devices(i03, fake_with_ophyd_sim=True)
    devices_b = make_all_devices(i03, fake_with_ophyd_sim=True)
    for device_name in devices_a.keys():
        assert devices_a[device_name] is devices_b[device_name]


def test_clear_devices():
    devices = make_all_devices(i03, fake_with_ophyd_sim=True)
    assert len(i03.ACTIVE_DEVICES) == len(devices.keys())
    i03.clear_devices()
    assert i03.ACTIVE_DEVICES == {}


def test_device_is_new_after_clearing():
    def _make_devices_and_get_id():
        return [
            id(device)
            for _, device in make_all_devices(i03, fake_with_ophyd_sim=True).items()
        ]

    ids_1 = [_make_devices_and_get_id()]
    ids_2 = [_make_devices_and_get_id()]
    assert ids_1 == ids_2
    i03.clear_devices()
    ids_3 = [_make_devices_and_get_id()]
    assert ids_1 != ids_3


def test_create_point_on_invalid_number_of_args():
    with pytest.raises(TypeError):
        create_point(1)
    with pytest.raises(TypeError):
        create_point()
    with pytest.raises(TypeError):
        create_point(7, 45, 23, 2, 1, 4)


def test_create_point_creates_zero_array_given_none_type_args():
    np.testing.assert_equal(np.array([0, 0, 5]), create_point(None, None, 5))


def test_create_point_returns_correct_array_size():
    assert create_point(5, 2).shape == (2,)
    assert create_point(5, 2, 4).shape == (3,)
