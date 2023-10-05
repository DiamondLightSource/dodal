from unittest.mock import ANY, MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine as RE
from ophyd import Device
from ophyd.device import Device as OphydV1Device
from ophyd.sim import FakeEpicsSignal
from ophyd_async.core import Device as OphydV2Device

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
    beamline_utils.clear_devices()
    dev1 = beamline_utils.device_instantiation(  # noqa
        Zebra, "device", "", False, False, None
    )
    with pytest.raises(TypeError):
        dev2 = beamline_utils.device_instantiation(
            Smargon, "device", "", False, False, None
        )
    beamline_utils.clear_device("device")
    dev2 = beamline_utils.device_instantiation(  # noqa
        Smargon, "device", "", False, False, None
    )
    assert dev1.name == dev2.name
    assert type(dev1) != type(dev2)
    assert dev1 not in beamline_utils.ACTIVE_DEVICES.values()
    assert dev2 in beamline_utils.ACTIVE_DEVICES.values()


def test_instantiate_function_fake_makes_fake():
    fake_zeb: Zebra = beamline_utils.device_instantiation(
        i03.Zebra, "zebra", "", True, True, None
    )
    assert isinstance(fake_zeb, Device)
    assert isinstance(fake_zeb.pc.arm_source, FakeEpicsSignal)


def test_clear_devices():
    beamline_utils.clear_devices()
    devices = make_all_devices(i03, fake_with_ophyd_sim=True)
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices.keys())
    beamline_utils.clear_devices()
    assert beamline_utils.ACTIVE_DEVICES == {}


def test_device_is_new_after_clearing():
    beamline_utils.clear_devices()

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


@pytest.mark.parametrize(
    "kwargs,expected_timeout", [({}, 5.0), ({"timeout": 15.0}, 15.0)]
)
def test_wait_for_v1_device_connection_passes_through_timeout(kwargs, expected_timeout):
    device = OphydV1Device(name="")
    device.wait_for_connection = MagicMock()

    beamline_utils._wait_for_connection(device, **kwargs)

    device.wait_for_connection.assert_called_once_with(timeout=expected_timeout)


@pytest.mark.parametrize(
    "kwargs,expected_timeout", [({}, 5.0), ({"timeout": 15.0}, 15.0)]
)
@patch("dodal.beamlines.beamline_utils.call_in_bluesky_event_loop", autospec=True)
def test_wait_for_v2_device_connection_passes_through_timeout(
    call_in_bluesky_el, kwargs, expected_timeout
):
    RE()
    device = OphydV2Device()

    beamline_utils._wait_for_connection(device, **kwargs)

    call_in_bluesky_el.assert_called_once_with(ANY, expected_timeout)
