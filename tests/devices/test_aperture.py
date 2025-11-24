import pytest
from ophyd_async.core import init_devices

from dodal.devices.aperture import Aperture


@pytest.fixture
async def fake_aperture():
    with init_devices(mock=True):
        fake_aperture = Aperture(prefix="test_ap", name="aperture")
    return fake_aperture


def test_aperture_can_be_created(fake_aperture: Aperture):
    assert isinstance(fake_aperture, Aperture)
