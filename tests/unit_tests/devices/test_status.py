import pytest
from ophyd import Component, Device, EpicsSignalRO
from ophyd.sim import make_fake_device


class FakeDevice(Device):
    pv = Component(EpicsSignalRO, "test")


@pytest.fixture
def fake_device():
    MyFakeDevice = make_fake_device(FakeDevice)
    fake_device = MyFakeDevice(name="test fake_device")
    return fake_device
