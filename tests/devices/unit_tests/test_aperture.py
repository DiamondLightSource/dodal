import pytest
from ophyd.sim import make_fake_device

from dodal.devices.aperture import Aperture


@pytest.fixture
async def fake_aperture():
    FakeAperture = make_fake_device(Aperture)
    fake_aperture: Aperture = FakeAperture(prefix="test_ap", name="aperture")
    await fake_aperture.connect(mock=True)
    return fake_aperture


def test_aperture_can_be_created(fake_aperture: Aperture):
    assert isinstance(fake_aperture, Aperture)
