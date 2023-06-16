import pytest
from ophyd import Component, Device, EpicsSignalRO
from ophyd.sim import make_fake_device

from dodal.devices.status import await_value


class FakeDevice(Device):
    pv: EpicsSignalRO = Component(EpicsSignalRO, "test")


@pytest.fixture
def fake_device():
    MyFakeDevice = make_fake_device(FakeDevice)
    fake_device = MyFakeDevice(name="test")
    return fake_device


def test_await_value_on_idle_pv(fake_device):
    fake_device.pv.sim_put(2)
    await_value(fake_device.pv, 2).wait()
