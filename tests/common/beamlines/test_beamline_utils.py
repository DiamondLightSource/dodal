import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine as RE
from ophyd import Device
from ophyd.device import Device as OphydV1Device
from ophyd.sim import FakeEpicsSignal
from ophyd_async.core import Device as OphydV2Device
from ophyd_async.core import StandardReadable

from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils
from dodal.devices.beamstop import BeamStop
from dodal.devices.eiger import EigerDetector
from dodal.devices.smargon import Smargon
from dodal.devices.zebra import Zebra
from dodal.log import LOGGER
from dodal.utils import make_all_devices

from ...conftest import mock_beamline_module_filepaths


@pytest.fixture(autouse=True)
def flush_event_loop_on_finish(event_loop):
    # wait for the test function to complete
    yield None

    if pending_tasks := asyncio.all_tasks(event_loop):
        LOGGER.warning(f"Waiting for pending tasks to complete {pending_tasks}")
        event_loop.run_until_complete(asyncio.gather(*pending_tasks))


@pytest.fixture(autouse=True)
def setup():
    beamline_utils.clear_devices()
    mock_beamline_module_filepaths("i03", i03)


def test_instantiate_function_makes_supplied_device():
    device_types = [Zebra, BeamStop, Smargon]
    for device in device_types:
        dev = beamline_utils.device_instantiation(
            device, device.__name__, "", False, True, None
        )
        assert isinstance(dev, device)


def test_instantiating_different_device_with_same_name():
    dev1 = beamline_utils.device_instantiation(  # noqa
        Zebra, "device", "", False, True, None
    )
    with pytest.raises(TypeError):
        dev2 = beamline_utils.device_instantiation(
            Smargon, "device", "", False, True, None
        )
    beamline_utils.clear_device("device")
    dev2 = beamline_utils.device_instantiation(  # noqa
        Smargon, "device", "", False, True, None
    )
    assert dev1.name == dev2.name
    assert type(dev1) is not type(dev2)
    assert dev1 not in beamline_utils.ACTIVE_DEVICES.values()
    assert dev2 in beamline_utils.ACTIVE_DEVICES.values()


def test_instantiate_v1_function_fake_makes_fake():
    eiger: EigerDetector = beamline_utils.device_instantiation(
        EigerDetector, "eiger", "", True, True, None
    )
    assert isinstance(eiger, Device)
    assert isinstance(eiger.stale_params, FakeEpicsSignal)


def test_instantiate_v2_function_fake_makes_fake():
    RE()
    fake_zeb: Zebra = beamline_utils.device_instantiation(
        i03.Zebra, "zebra", "", True, True, None
    )
    assert isinstance(fake_zeb, StandardReadable)
    assert fake_zeb.pc.arm.armed.source.startswith("mock+ca")


def test_clear_devices(RE):
    devices, exceptions = make_all_devices(i03, fake_with_ophyd_sim=True)
    assert (
        len(beamline_utils.ACTIVE_DEVICES) == len(devices.keys())
        and len(exceptions) == 0
    )
    beamline_utils.clear_devices()
    assert beamline_utils.ACTIVE_DEVICES == {}


def test_device_is_new_after_clearing(RE):
    def _make_devices_and_get_id():
        devices, _ = make_all_devices(i03, fake_with_ophyd_sim=True)
        return [id(device) for device in devices.values()]

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

    beamline_utils.wait_for_connection(device, **kwargs)

    device.wait_for_connection.assert_called_once_with(timeout=expected_timeout)


@pytest.mark.parametrize(
    "kwargs,expected_timeout", [({}, 5.0), ({"timeout": 15.0}, 15.0)]
)
@patch(
    "dodal.common.beamlines.beamline_utils.v2_device_wait_for_connection",
    new=AsyncMock(),
)
def test_wait_for_v2_device_connection_passes_through_timeout(kwargs, expected_timeout):
    RE()
    device = OphydV2Device()
    device.connect = MagicMock()

    beamline_utils.wait_for_connection(device, **kwargs)

    device.connect.assert_called_once_with(
        mock=ANY,
        timeout=expected_timeout,
    )
