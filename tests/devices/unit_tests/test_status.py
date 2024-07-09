from time import sleep
from unittest.mock import patch

import pytest
from ophyd import Component, Device, EpicsSignalRO
from ophyd.sim import make_fake_device

from dodal.devices.status import await_value_and_warn_if_long, await_value_in_list


class FakeDevice(Device):
    pv = Component(EpicsSignalRO, "test")


@pytest.fixture
def fake_device():
    MyFakeDevice = make_fake_device(FakeDevice)
    fake_device = MyFakeDevice(name="test fake_device")
    return fake_device


@pytest.mark.parametrize("awaited_value", [(1), (5.3), (False)])
def test_await_value_in_list_with_no_list_parameter_fails(awaited_value, fake_device):
    with pytest.raises(TypeError):
        await_value_in_list(fake_device.pv, awaited_value)


def test_await_value_in_list_success(fake_device):
    status = await_value_in_list(fake_device.pv, [1, 2, 3, 4, 5])
    assert status.done is False
    fake_device.pv.sim_put(5)  # type: ignore
    status.wait(timeout=1)


@patch("dodal.devices.status.LOGGER")
def test_await_status_warn_at_warns_at(mock_logger, fake_device):
    status = await_value_and_warn_if_long(
        fake_device.pv,
        expected_value=5,
        timeout=1,
        warn_at=0.1,
        warning_extra_msg="status took long",  # type: ignore
    )
    mock_logger.assert_not_called()
    assert status.done is False
    sleep(0.12)
    fake_device.pv.sim_put(5)  # type: ignore
    status.wait()
    assert status.done is True
    mock_logger.warning.assert_called()
    assert "status took long" in mock_logger.warning.call_args.args[0]


@patch("dodal.devices.status.LOGGER")
def test_await_status_doesnt_warn_before_warns_at(mock_logger, fake_device):
    status = await_value_and_warn_if_long(
        fake_device.pv,
        expected_value=5,
        timeout=1,
        warn_at=0.1,
        warning_extra_msg="status took long",  # type: ignore
    )
    mock_logger.assert_not_called()
    assert status.done is False
    fake_device.pv.sim_put(5)  # type: ignore
    status.wait()
    assert status.done is True
    mock_logger.warning.assert_not_called()
