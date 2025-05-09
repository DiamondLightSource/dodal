import math

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices

from dodal.beamlines import aithre
from dodal.devices.aithre_lasershaping.goniometer import Goniometer
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
def goniometer(RE: RunEngine) -> Goniometer:
    with init_devices(mock=True):
        gonio = aithre.goniometer(connect_immediately=True, mock=True)
    patch_motor(gonio.omega)
    patch_motor(gonio.sampy)
    patch_motor(gonio.sampz)
    return gonio


async def test_vertical_position_set(goniometer: Goniometer):
    await goniometer._set(value=5)
    assert await goniometer.vertical_position.get_value() == 5


async def test_vertical_position_get(goniometer: Goniometer):
    assert goniometer._get(math.sqrt(3), 1, 30) == pytest.approx(2)
