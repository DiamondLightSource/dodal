import pytest
from ophyd import Device
from ophyd.sim import FakeEpicsSignal

from dodal.beamlines import beamline_utils, i03
from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.smargon import Smargon
from dodal.devices.zebra import Zebra
from dodal.utils import make_all_devices


def test_instantiate_function_makes_supplied_device():
    device_types = [Zebra, ApertureScatterguard, Smargon]
    for device in device_types:
        beamline_utils.clear_devices()
        dev = beamline_utils.device_instantiation(
            device, "device", "", False, False, None
        )
        assert isinstance(dev, device)


def test_instantiating_different_device_with_same_name():
    dev1 = beamline_utils.device_instantiation(
        Zebra, "device", "", False, False, None
    )  # noqa
    with pytest.raises(TypeError):
        dev2 = beamline_utils.device_instantiation(  # noqa
            Smargon, "device", "", False, False, None
        )
    beamline_utils.clear_device("device")
    dev2 = beamline_utils.device_instantiation(
        Smargon, "device", "", False, False, None
    )  # noqa
    assert dev1 is dev2


def test_instantiate_function_fake_makes_fake():
    fake_zeb: Zebra = beamline_utils.device_instantiation(
        i03.Zebra, "zebra", "", True, True, None
    )
    assert isinstance(fake_zeb, Device)
    assert isinstance(fake_zeb.pc.arm_source, FakeEpicsSignal)


def test_clear_devices():
    devices = make_all_devices(i03, fake_with_ophyd_sim=True)
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices.keys())
    beamline_utils.clear_devices()
    assert beamline_utils.ACTIVE_DEVICES == {}


def test_device_is_new_after_clearing():
    def _make_devices_and_get_id():
        return [
            id(device)
            for _, device in make_all_devices(i03, fake_with_ophyd_sim=True).items()
        ]

    ids_1 = [_make_devices_and_get_id()]
    ids_2 = [_make_devices_and_get_id()]
    assert ids_1 == ids_2
    beamline_utils.clear_devices()
    ids_3 = [_make_devices_and_get_id()]
    assert ids_1 != ids_3
