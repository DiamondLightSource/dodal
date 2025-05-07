import math
from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.motors import Axis, SixAxisGonio
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


@pytest.fixture
def y_up_six_axis_gonio(RE: RunEngine) -> SixAxisGonio:
    with init_devices(mock=True):
        gonio = SixAxisGonio(
            "", upward_axis_at_0=Axis.Y, upward_axis_at_minus_90=Axis.Z
        )
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
    "i_set_value, omega_set_value, expected_horz, expected_vert",
    [[2, 60, 2, 0], [-10, -45, -10, 0]],
)
async def test_i_signal_for_default_axes(
    six_axis_gonio: SixAxisGonio,
    i_set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await six_axis_gonio.omega.set(omega_set_value)
    await six_axis_gonio.i.set(i_set_value)

    assert await six_axis_gonio.x.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_vert
    )


@pytest.mark.parametrize(
    "j_set_value, omega_set_value, expected_horz, expected_vert",
    [
        [2, 60, math.sqrt(3), 1],
        [-10, 390, -5, -5 * math.sqrt(3)],
        [0.5, -135, -math.sqrt(2) / 4, -math.sqrt(2) / 4],
        [1, 0, 0, 1],
    ],
)
async def test_j_signal_for_default_axes(
    six_axis_gonio: SixAxisGonio,
    j_set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await six_axis_gonio.omega.set(omega_set_value)
    await six_axis_gonio.j.set(j_set_value)

    assert await six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_vert
    )

    await six_axis_gonio.j.set(j_set_value * 2)
    assert await six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_horz * 2
    )
    assert await six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_vert * 2
    )


@pytest.mark.parametrize(
    "i_set_value, omega_set_value, expected_horz, expected_vert",
    [[2, 60, 2, 0], [-10, -45, -10, 0]],
)
async def test_i_signal_for_rotated_axes(
    y_up_six_axis_gonio: SixAxisGonio,
    i_set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await y_up_six_axis_gonio.omega.set(omega_set_value)
    await y_up_six_axis_gonio.i.set(i_set_value)

    assert await y_up_six_axis_gonio.x.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await y_up_six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_vert
    )


@pytest.mark.parametrize(
    "j_set_value, omega_set_value, expected_horz, expected_vert",
    [
        [2, 60, 1, math.sqrt(3)],
        [-10, 390, -5 * math.sqrt(3), -5],
        [0.5, -135, -math.sqrt(2) / 4, -math.sqrt(2) / 4],
        [1, 0, 1, 0],
    ],
)
async def test_j_signal_for_rotated_axes(
    y_up_six_axis_gonio: SixAxisGonio,
    j_set_value: float,
    omega_set_value: float,
    expected_horz: float,
    expected_vert: float,
):
    await y_up_six_axis_gonio.omega.set(omega_set_value)
    await y_up_six_axis_gonio.j.set(j_set_value)

    assert await y_up_six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_horz
    )
    assert await y_up_six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_vert
    )

    await y_up_six_axis_gonio.j.set(j_set_value * 2)
    assert await y_up_six_axis_gonio.y.user_readback.get_value() == pytest.approx(
        expected_horz * 2
    )
    assert await y_up_six_axis_gonio.z.user_readback.get_value() == pytest.approx(
        expected_vert * 2
    )


async def test_get_j(y_up_six_axis_gonio: SixAxisGonio):
    await y_up_six_axis_gonio.j.set(5)
    assert await y_up_six_axis_gonio.j.get_value() == 5


async def test_get_i(y_up_six_axis_gonio: SixAxisGonio):
    await y_up_six_axis_gonio.i.set(5)
    assert await y_up_six_axis_gonio.i.get_value() == 5


@pytest.mark.parametrize(
    "input_axis, expected_axis",
    [
        [Axis.X, "x"],
        [Axis.Y, "y"],
        [Axis.Z, "z"],
    ],
)
async def test_get_axis_signal(
    six_axis_gonio: SixAxisGonio, input_axis: Axis, expected_axis: str
):
    assert six_axis_gonio._get_axis_signal(input_axis) == getattr(
        six_axis_gonio, expected_axis
    )
