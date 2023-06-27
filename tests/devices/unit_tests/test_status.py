import pytest
from ophyd import Component, Device, EpicsSignalRO
from ophyd.sim import make_fake_device

from dodal.devices.status import await_value_in_list


class FakeDevice(Device):
    pv: EpicsSignalRO = Component(EpicsSignalRO, "test")


@pytest.fixture
def fake_device():
    MyFakeDevice = make_fake_device(FakeDevice)
    fake_device = MyFakeDevice(name="test")
    return fake_device


@pytest.mark.parametrize("awaited_value", [(1), (5.3), (False)])
def test_await_value_in_list_with_no_list_parameter_fails(awaited_value, fake_device):
    with pytest.raises(TypeError):
        await_value_in_list(fake_device.pv, awaited_value)


def test_await_value_in_list_success(fake_device):
    status = await_value_in_list(fake_device.pv, [1, 2, 3, 4, 5])
    assert status.done is False
    fake_device.pv.sim_put(5)
    status.wait(timeout=1)
