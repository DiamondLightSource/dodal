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


@pytest.mark.parametrize(
    "vertical_set_value, omega_set_value, expected_horz, expected_vert",
    [
        [2, 60, 1, math.sqrt(3)],
        [-10, 390, -5 * math.sqrt(3), -5],
        [0.5, -135, -math.sqrt(2) / 4, -math.sqrt(2) / 4],
        [1, 0, 1, 0],
        [-1.5, 90, 0, -1.5],
    ],
)
async def test_vertical_signal_set(
    goniometer: Goniometer,
    vertical_set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await goniometer.omega.set(omega_set_value)
    await goniometer.vertical_position.set(vertical_set_value)

    assert await goniometer.sampz.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await goniometer.sampy.user_readback.get_value() == pytest.approx(
        expected_vert
    )

    await goniometer.vertical_position.set(vertical_set_value * 2)
    assert await goniometer.sampz.user_readback.get_value() == pytest.approx(
        expected_horz * 2
    )
    assert await goniometer.sampy.user_readback.get_value() == pytest.approx(
        expected_vert * 2
    )
