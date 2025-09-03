import math
from collections.abc import Generator

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.motors import SixAxisGonio
from dodal.devices.util.test_utils import patch_all_motors


@pytest.fixture
def six_axis_gonio() -> Generator[SixAxisGonio]:
    with init_devices(mock=True):
        gonio = SixAxisGonio("")

    with patch_all_motors(gonio):
        yield gonio


async def test_reading_six_axis_gonio(six_axis_gonio: SixAxisGonio):
    await assert_reading(
        six_axis_gonio,
        {
            "gonio-omega": partial_reading(0.0),
            "gonio-kappa": partial_reading(0.0),
            "gonio-phi": partial_reading(0.0),
            "gonio-z": partial_reading(0.0),
            "gonio-y": partial_reading(0.0),
            "gonio-x": partial_reading(0.0),
        },
    )


@pytest.mark.parametrize(
    "set_value, omega_set_value, expected_horz, expected_vert",
    [
        [2, 60, math.sqrt(3), 1],
        [-10, 390, -5, -5 * math.sqrt(3)],
        [0.5, -135, -math.sqrt(2) / 4, -math.sqrt(2) / 4],
        [1, 0, 0, 1],
    ],
)
async def test_vertical_in_lab_space_for_default_axes(
    six_axis_gonio: SixAxisGonio,
    set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await six_axis_gonio.omega.set(omega_set_value)
    await six_axis_gonio.vertical_in_lab_space.set(set_value)

    assert await six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_vert
    )

    await six_axis_gonio.vertical_in_lab_space.set(set_value * 2)
    assert await six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_horz * 2
    )
    assert await six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_vert * 2
    )


@pytest.mark.parametrize(
    "set_point",
    [
        -5,
        0,
        100,
        0.7654,
    ],
)
async def test_lab_vertical_round_trip(six_axis_gonio: SixAxisGonio, set_point: float):
    await six_axis_gonio.vertical_in_lab_space.set(set_point)
    assert await six_axis_gonio.vertical_in_lab_space.get_value() == set_point
