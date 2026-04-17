import math
from collections.abc import Generator, Iterable

import numpy as np
import pytest
from bluesky import RunEngine
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.motors import (
    SixAxisGonio,
    XThetaStage,
    XYStage,
    XYZAzimuthStage,
    XYZAzimuthTiltPolarStage,
    XYZAzimuthTiltStage,
    XYZPitchYawRollStage,
    XYZThetaStage,
    XYZWrappedOmegaStage,
)


@pytest.fixture
async def xyzt_stage() -> XYZThetaStage:
    async with init_devices(mock=True):
        xyzt_stage = XYZThetaStage("")
    return xyzt_stage


@pytest.fixture
async def xyza_stage() -> XYZAzimuthStage:
    async with init_devices(mock=True):
        xyza_stage = XYZAzimuthStage("")
    return xyza_stage


@pytest.fixture
async def xyzat_stage() -> XYZAzimuthTiltStage:
    async with init_devices(mock=True):
        xyzat_stage = XYZAzimuthTiltStage("")
    return xyzat_stage


@pytest.fixture
async def xyzatp_stage() -> XYZAzimuthTiltPolarStage:
    async with init_devices(mock=True):
        xyzatp_stage = XYZAzimuthTiltPolarStage("")
    return xyzatp_stage


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


@pytest.fixture()
async def xyz_wrapped_omega_stage(
    values_for_rotation: Iterable[float],
) -> XYZWrappedOmegaStage:
    input_value, current_real_value, expected_real_value = values_for_rotation

    async with init_devices(mock=True):
        xyz_wrapped_omega_stage = XYZWrappedOmegaStage("BL03I-MO-SGON-01:")
    set_mock_value(xyz_wrapped_omega_stage.omega.user_readback, current_real_value)
    return xyz_wrapped_omega_stage


async def test_setting_xy_position_table(xyzt_stage: XYZThetaStage):
    """Test setting x and y positions on the Table using the ophyd_async mock tools."""
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
    """Test setting x and y positions on the Table using the ophyd_async mock tools."""
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
    "x, y, z, azimuth",
    [
        (0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0),
    ],
)
async def test_setting_xyza_position_table(
    xyza_stage: XYZAzimuthStage,
    x: float,
    y: float,
    z: float,
    azimuth: float,
):
    set_mock_value(xyza_stage.x.user_readback, x)
    set_mock_value(xyza_stage.y.user_readback, y)
    set_mock_value(xyza_stage.z.user_readback, z)
    set_mock_value(xyza_stage.azimuth.user_readback, azimuth)

    await assert_reading(
        xyza_stage,
        {
            "xyza_stage-x": partial_reading(x),
            "xyza_stage-y": partial_reading(y),
            "xyza_stage-z": partial_reading(z),
            "xyza_stage-azimuth": partial_reading(azimuth),
        },
    )


@pytest.mark.parametrize(
    "x, y, z, azimuth, tilt",
    [
        (0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0),
        (1.23, 2.40, 3.51, 24.0, 1.0),
    ],
)
async def test_setting_xyzat_position_table(
    xyzat_stage: XYZAzimuthTiltStage,
    x: float,
    y: float,
    z: float,
    azimuth: float,
    tilt: float,
):
    set_mock_value(xyzat_stage.x.user_readback, x)
    set_mock_value(xyzat_stage.y.user_readback, y)
    set_mock_value(xyzat_stage.z.user_readback, z)
    set_mock_value(xyzat_stage.azimuth.user_readback, azimuth)
    set_mock_value(xyzat_stage.tilt.user_readback, tilt)

    await assert_reading(
        xyzat_stage,
        {
            "xyzat_stage-x": partial_reading(x),
            "xyzat_stage-y": partial_reading(y),
            "xyzat_stage-z": partial_reading(z),
            "xyzat_stage-azimuth": partial_reading(azimuth),
            "xyzat_stage-tilt": partial_reading(tilt),
        },
    )


@pytest.mark.parametrize(
    "x, y, z, azimuth, tilt, polar",
    [
        (0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0, 1.0, 2.0),
    ],
)
async def test_setting_xyzatp_position_table(
    xyzatp_stage: XYZAzimuthTiltPolarStage,
    x: float,
    y: float,
    z: float,
    azimuth: float,
    tilt: float,
    polar: float,
) -> None:
    set_mock_value(xyzatp_stage.x.user_readback, x)
    set_mock_value(xyzatp_stage.y.user_readback, y)
    set_mock_value(xyzatp_stage.z.user_readback, z)
    set_mock_value(xyzatp_stage.polar.user_readback, polar)
    set_mock_value(xyzatp_stage.azimuth.user_readback, azimuth)
    set_mock_value(xyzatp_stage.tilt.user_readback, tilt)

    await assert_reading(
        xyzatp_stage,
        {
            "xyzatp_stage-x": partial_reading(x),
            "xyzatp_stage-y": partial_reading(y),
            "xyzatp_stage-z": partial_reading(z),
            "xyzatp_stage-azimuth": partial_reading(azimuth),
            "xyzatp_stage-tilt": partial_reading(tilt),
            "xyzatp_stage-polar": partial_reading(polar),
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
    """Test setting positions on the Table using the ophyd_async mock tools."""
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


async def test_setting_xy_stage(xy_stage: XYStage):
    """Test setting x and y positions on the XYStage using ophyd_async mock tools."""
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


@pytest.mark.parametrize("values_for_rotation", [[0, 0, 0]], indirect=True)
async def test_reading_xyz_wrapped_omega_gonio(
    xyz_wrapped_omega_stage: XYZWrappedOmegaStage, values_for_rotation: Iterable[float]
):
    await assert_reading(
        xyz_wrapped_omega_stage,
        {
            "xyz_wrapped_omega_stage-omega": partial_reading(0.0),
            "xyz_wrapped_omega_stage-z": partial_reading(0.0),
            "xyz_wrapped_omega_stage-y": partial_reading(0.0),
            "xyz_wrapped_omega_stage-x": partial_reading(0.0),
            "xyz_wrapped_omega_stage-wrapped_omega-phase": partial_reading(0.0),
            "xyz_wrapped_omega_stage-wrapped_omega-offset_and_phase": partial_reading(
                np.array([0, 0])
            ),
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


@pytest.mark.parametrize(
    "real_value, expected_phase",
    [
        [0, 0],
        [0.001, 0.001],
        [360, 0],
        [-359.999, 0.001],
        [-360, 0],
        [-180.001, 179.999],
        [-179.999, 180.001],
        [-0.001, 359.999],
        [180.001, 180.001],
        [360.001, 0.001],
        [719.999, 359.999],
        [720.001, 0.001],
        [10000 * 360 + 0.001, 0.001],
        [-10000 * 360 - 0.001, 359.999],
    ],
)
async def test_mod_360_read(
    real_value: float,
    expected_phase: float,
    xyz_wrapped_omega_stage: XYZWrappedOmegaStage,
):
    set_mock_value(xyz_wrapped_omega_stage.omega.user_readback, real_value)
    (
        offset,
        phase,
    ) = await xyz_wrapped_omega_stage.wrapped_omega.offset_and_phase.get_value()
    assert 0 <= expected_phase < 360
    assert math.isclose(phase, expected_phase, abs_tol=1e-6)
    assert math.isclose(phase + offset, real_value, abs_tol=1e-6)


@pytest.fixture(
    params=[
        [0, 0, 0],
        [0.001, 0, 0.001],
        [-5, 0, -5],
        [360, 0, 0],
        [-359.999, 0, 0.001],
        [-360, 0, 0],
        [-180.001, 0, 179.999],
        [-179.999, 0, -179.999],
        [-0.001, 0, -0.001],
        [0, 90, 0],
        [0.001, 90, 0.001],
        [360, 90, 0],
        [-359.999, 90, 0.001],
        [-360, 90, 0],
        [-180.001, 90, 179.999],
        [-179.999, 90, 180.001],
        [-0.001, 90, -0.001],
        [0, 90, 0],
        [0.001, 450, 360.001],
        [360, 450, 360],
        [-359.999, 450, 360.001],
        [-360, 450, 360],
        [-180.001, 450, 539.999],
        [-179.999, 450, 540.001],
        [-0.001, 450, 359.999],
        [180.001, -270, -179.999],
        [360.001, -270, -359.999],
        [719.999, -270, -360.001],
        [-720.001, 270, 359.999],
        [10000 * 360 + 0.001, 360000 - 90, 360000.001],
        [-10000 * 360 - 0.001, -360000 + 90, -360000.001],
    ],
    ids=lambda values: f"input={values[0]}, current={values[1]}, expected={values[2]}",
)
def values_for_rotation(
    request: pytest.FixtureRequest,
) -> Generator[tuple[float, float, float], None, None]:
    input_value, current_real_value, expected_real_value = request.param
    yield input_value, current_real_value, expected_real_value


async def test_mod_360_expected_direction_of_rotation_same_as_apparent_for_moves_apparently_less_than_180(
    values_for_rotation: Iterable[float], xyz_wrapped_omega_stage: XYZWrappedOmegaStage
):
    input_value, current_real_value, expected_real_value = values_for_rotation
    stage = xyz_wrapped_omega_stage

    current_readback = await stage.omega.user_readback.get_value()
    is_no_move = expected_real_value == current_real_value
    is_ge_than_180 = abs(input_value - current_readback) >= 180
    motion_in_same_direction_as_apparent = (input_value < current_readback) == (
        expected_real_value < current_real_value
    )
    assert is_no_move or is_ge_than_180 or motion_in_same_direction_as_apparent, (
        f"expected ({input_value} - {current_real_value}) same sign as ({expected_real_value} - {current_real_value})"
    )


async def test_mod_360_expected_actual_movement_never_more_than_180(
    values_for_rotation: tuple[float, float, float],
    xyz_wrapped_omega_stage: XYZWrappedOmegaStage,
):
    input_value, current_real_value, expected_real_value = values_for_rotation
    assert abs(expected_real_value - current_real_value) <= 180


async def test_mod_360_unwrap_computes_expected(
    values_for_rotation: tuple[float, float, float],
    xyz_wrapped_omega_stage: XYZWrappedOmegaStage,
    run_engine: RunEngine,
) -> None:
    input_value, current_real_value, expected_real_value = values_for_rotation
    stage = xyz_wrapped_omega_stage
    real_put = get_mock_put(stage.omega.user_setpoint)
    await stage.wrapped_omega.phase.set(input_value)
    real_put.assert_called_once()
    actual = real_put.mock_calls[0].args[0]
    assert math.isclose(actual, expected_real_value), (
        f"expected {expected_real_value} but was {actual}"
    )
