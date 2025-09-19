import math
from collections.abc import Generator

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.motors import (
    SixAxisGonio,
    XThetaStage,
    XYStage,
    XYZPitchYawRollStage,
    XYZThetaStage,
)
from dodal.testing import patch_all_motors


@pytest.fixture
async def xyzt_stage() -> XYZThetaStage:
    async with init_devices(mock=True):
        xyzt_stage = XYZThetaStage("")
    return xyzt_stage


@pytest.fixture
async def xy_stage() -> XYStage:
    async with init_devices(mock=True):
        xy_stage = XYStage("")
    return xy_stage


@pytest.fixture
async def xtheta_stage() -> XThetaStage:
    async with init_devices(mock=True):
        xtheta_stage = XThetaStage("")
    return xtheta_stage


@pytest.fixture
async def xyzpyr_stage() -> XYZPitchYawRollStage:
    async with init_devices(mock=True):
        xyzpyr_stage = XYZPitchYawRollStage("")
    return xyzpyr_stage


async def test_setting_xy_position_table(xyzt_stage: XYZThetaStage):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": partial_reading(0.0),
            "xyzt_stage-y": partial_reading(0.0),
            "xyzt_stage-z": partial_reading(0.0),
            "xyzt_stage-theta": partial_reading(0.0),
        },
    )

    # Call set to update the position
    set_mock_value(xyzt_stage.x.user_readback, 1.23)
    set_mock_value(xyzt_stage.y.user_readback, 4.56)

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": partial_reading(1.23),
            "xyzt_stage-y": partial_reading(4.56),
            "xyzt_stage-z": partial_reading(0),
            "xyzt_stage-theta": partial_reading(0.0),
        },
    )


async def test_setting_xyztheta_position_table(xyzt_stage: XYZThetaStage):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """
    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": partial_reading(0.0),
            "xyzt_stage-y": partial_reading(0.0),
            "xyzt_stage-z": partial_reading(0.0),
            "xyzt_stage-theta": partial_reading(0.0),
        },
    )

    # Call set to update the position
    set_mock_value(xyzt_stage.x.user_readback, 1.23)
    set_mock_value(xyzt_stage.y.user_readback, 4.56)
    set_mock_value(xyzt_stage.z.user_readback, 7.89)
    set_mock_value(xyzt_stage.theta.user_readback, 10.11)

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": partial_reading(1.23),
            "xyzt_stage-y": partial_reading(4.56),
            "xyzt_stage-z": partial_reading(7.89),
            "xyzt_stage-theta": partial_reading(10.11),
        },
    )


@pytest.mark.parametrize(
    "x, y, z, pitch, yaw, roll",
    [
        (0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0, 12.0, 3.56),
    ],
)
async def test_setting_xyzpyr_position_table(
    xyzpyr_stage: XYZPitchYawRollStage,
    x: float,
    y: float,
    z: float,
    pitch: float,
    yaw: float,
    roll: float,
):
    """
    Test setting positions on the Table using the ophyd_async mock tools.
    """
    # Call set to update the position
    set_mock_value(xyzpyr_stage.x.user_readback, x)
    set_mock_value(xyzpyr_stage.y.user_readback, y)
    set_mock_value(xyzpyr_stage.z.user_readback, z)
    set_mock_value(xyzpyr_stage.pitch.user_readback, pitch)
    set_mock_value(xyzpyr_stage.yaw.user_readback, yaw)
    set_mock_value(xyzpyr_stage.roll.user_readback, roll)

    await assert_reading(
        xyzpyr_stage,
        {
            "xyzpyr_stage-x": partial_reading(x),
            "xyzpyr_stage-y": partial_reading(y),
            "xyzpyr_stage-z": partial_reading(z),
            "xyzpyr_stage-pitch": partial_reading(pitch),
            "xyzpyr_stage-yaw": partial_reading(yaw),
            "xyzpyr_stage-roll": partial_reading(roll),
        },
    )


async def test_setting(xy_stage: XYStage):
    """
    Test setting x and y positions on the XYStage using ophyd_async mock tools.
    """

    await assert_reading(
        xy_stage,
        {"xy_stage-x": partial_reading(0.0), "xy_stage-y": partial_reading(0.0)},
    )

    # Call set to update the position
    set_mock_value(xy_stage.x.user_readback, 5)
    set_mock_value(xy_stage.y.user_readback, 5)

    await assert_reading(
        xy_stage,
        {"xy_stage-x": partial_reading(5.0), "xy_stage-y": partial_reading(5.0)},
    )


async def test_reading_training_rig(xtheta_stage: XThetaStage):
    await assert_reading(
        xtheta_stage,
        {
            "xtheta_stage-x": partial_reading(0.0),
            "xtheta_stage-theta": partial_reading(0.0),
        },
    )


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
