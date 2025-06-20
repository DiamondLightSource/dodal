import math
from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.motors import SixAxisGonio
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
def six_axis_gonio(RE: RunEngine) -> SixAxisGonio:
    with init_devices(mock=True):
        gonio = SixAxisGonio("")
    patch_motor(gonio.omega)
    patch_motor(gonio.z)
    patch_motor(gonio.y)
    patch_motor(gonio.x)

    return gonio


async def test_reading_six_axis_gonio(six_axis_gonio: SixAxisGonio):
    await assert_reading(
        six_axis_gonio,
        {
            "gonio-omega": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-kappa": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-phi": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-z": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-y": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-x": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-_horizontal_stage_axis": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "gonio-_vertical_stage_axis": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
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

@pytest.mark.parametrize("set_point",
    [
        -5, 0, 100, 0.7654,
    ],
)
async def test_lab_vertical_round_trip(six_axis_gonio: SixAxisGonio, set_point: float):
    await six_axis_gonio.vertical_in_lab_space.set(set_point)
    assert await six_axis_gonio.vertical_in_lab_space.get_value() == set_point
