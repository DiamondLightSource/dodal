from collections.abc import Mapping

import bluesky.plan_stubs as bps
import numpy as np
import pytest
from bluesky.plans import grid_scan, scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_emitted

from dodal.devices.beamlines.i10.rasor.halbach import (
    HalbachLookupTable,
    HalbachMagnetArrayController,
    HalbachSetpoint,
)
from tests.devices.beamlines.i10.test_data import HALBACH_LUT_CSV


@pytest.fixture(scope="module")
def halbach_lut() -> HalbachLookupTable:
    return HalbachLookupTable.from_csv(HALBACH_LUT_CSV)


@pytest.fixture
async def halbach_controller(
    halbach_lut: HalbachLookupTable,
) -> HalbachMagnetArrayController:
    async with init_devices(mock=True):
        controller = HalbachMagnetArrayController(
            prefix="anythinggoes:",
            lut=halbach_lut,
            waypoint_step_mt=0.0,
            waypoint_step_deg=0.0,
        )
    for motor in controller.motors:
        callback_on_mock_put(
            motor.user_setpoint,
            lambda pos, *_, m=motor, **__: set_mock_value(m.user_readback, float(pos)),
        )
    return controller


async def test_set_raises_on_empty_setpoint(
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    with pytest.raises(
        ValueError, match="At least one of h_mt or field_angle_z_deg must be provided"
    ):
        await halbach_controller.set(HalbachSetpoint())


@pytest.mark.parametrize(
    "invalid_setpoint",
    [
        HalbachSetpoint(h_mt=180.0, field_angle_z_deg=0.0),
        HalbachSetpoint(h_mt=-171.0, field_angle_z_deg=0.0),
        HalbachSetpoint(h_mt=0.0, field_angle_z_deg=115.0),
        HalbachSetpoint(h_mt=0.0, field_angle_z_deg=-115.0),
    ],
)
async def test_set_rejects_fields_outside_calibrated_lut(
    halbach_controller: HalbachMagnetArrayController,
    invalid_setpoint: HalbachSetpoint,
) -> None:
    with pytest.raises(ValueError, match="outside calibrated LUT bounds"):
        await halbach_controller.set(invalid_setpoint)


@pytest.mark.parametrize(
    ("current_deg", "lut_target_deg", "expected_deg"),
    [
        (
            [0.0, 0.0, 0.0, 0.0],
            [10.0, 350.0, 180.0, -10.0],
            [10.0, -10.0, 180.0, -10.0],
        ),
        (
            [710.0, -350.0, 370.0, 170.0],
            [10.0, 350.0, 350.0, 190.0],
            [730.0, -370.0, 350.0, 190.0],
        ),
    ],
)
def test_compute_shortest_path_targets(
    current_deg: list[float],
    lut_target_deg: list[float],
    expected_deg: list[float],
) -> None:
    targets = HalbachMagnetArrayController.compute_shortest_path_targets(
        np.array(current_deg),
        np.array(lut_target_deg),
    )
    assert targets == pytest.approx(expected_deg)


@pytest.mark.parametrize(
    ("step_mt", "step_deg", "start", "target", "expected_waypoints"),
    [
        (0.0, 0.0, (0.0, 0.0), (100.0, 45.0), [(100.0, 45.0)]),
        (50.0, 30.0, (0.0, 0.0), (40.0, 20.0), [(40.0, 20.0)]),
        (50.0, 0.0, (0.0, 0.0), (120.0, 0.0), [(40.0, 0.0), (80.0, 0.0), (120.0, 0.0)]),
        (
            0.0,
            15.0,
            (0.0, 0.0),
            (0.0, -45.0),
            [(0.0, -15.0), (0.0, -30.0), (0.0, -45.0)],
        ),
        (
            50.0,
            10.0,
            (0.0, 0.0),
            (50.0, 40.0),
            [(12.5, 10.0), (25.0, 20.0), (37.5, 30.0), (50.0, 40.0)],
        ),
    ],
)
async def test_calculate_waypoints(
    halbach_controller: HalbachMagnetArrayController,
    step_mt: float,
    step_deg: float,
    start: tuple[float, float],
    target: tuple[float, float],
    expected_waypoints: list[tuple[float, float]],
) -> None:
    await halbach_controller.waypoint_step_mt.set(step_mt)
    await halbach_controller.waypoint_step_deg.set(step_deg)
    waypoints = await halbach_controller.calculate_waypoints(
        start_h_mt=start[0],
        start_angle_deg=start[1],
        target_h_mt=target[0],
        target_angle_deg=target[1],
    )
    assert waypoints == pytest.approx(expected_waypoints)


async def test_set_moves_motors_and_updates_setpoints(
    halbach_controller: HalbachMagnetArrayController,
    halbach_lut: HalbachLookupTable,
) -> None:
    lut_deg = halbach_lut.interpolate(-170.0, 0.0)
    expected_deg = halbach_controller.compute_shortest_path_targets(
        np.zeros(4), lut_deg
    )

    await halbach_controller.set(HalbachSetpoint(h_mt=-170.0, field_angle_z_deg=0.0))

    for motor, exp_pos in zip(halbach_controller.motors, expected_deg, strict=True):
        get_mock_put(motor.user_setpoint).assert_called_once_with(
            pytest.approx(exp_pos, abs=1e-4)
        )

    assert await halbach_controller.field.get_value() == -170.0
    assert await halbach_controller.angle.get_value() == 0.0


@pytest.mark.parametrize(
    ("partial_setpoint", "expected_h", "expected_angle"),
    [
        (HalbachSetpoint(h_mt=-60.0), -60.0, 20.0),
        (HalbachSetpoint(field_angle_z_deg=-15.0), 120.0, -15.0),
    ],
)
async def test_partial_setpoint(
    halbach_controller: HalbachMagnetArrayController,
    partial_setpoint: HalbachSetpoint,
    expected_h: float,
    expected_angle: float,
) -> None:
    await halbach_controller.set(HalbachSetpoint(h_mt=120.0, field_angle_z_deg=20.0))
    await halbach_controller.set(partial_setpoint)

    assert await halbach_controller.field.get_value() == pytest.approx(expected_h)
    assert await halbach_controller.angle.get_value() == pytest.approx(expected_angle)


async def test_field_move_keeps_angle(
    run_engine: RunEngine,
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    run_engine(bps.mv(halbach_controller.angle, -35.0))
    run_engine(bps.mv(halbach_controller.field, 120.0))

    assert await halbach_controller.field.get_value() == pytest.approx(120.0)
    assert await halbach_controller.angle.get_value() == pytest.approx(-35.0)


async def test_angle_move_leave_field(
    run_engine: RunEngine,
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    run_engine(bps.mv(halbach_controller.field, 120.0))
    run_engine(bps.mv(halbach_controller.angle, 20.0))

    assert await halbach_controller.field.get_value() == pytest.approx(120.0)
    assert await halbach_controller.angle.get_value() == pytest.approx(20.0)


async def test_shortest_path_relative_to_current_readback(
    halbach_controller: HalbachMagnetArrayController,
    halbach_lut: HalbachLookupTable,
) -> None:
    lut_deg = halbach_lut.interpolate(50.0, -30.0)
    initial_rbv = lut_deg + 720.0 + np.array([5.0, -4.0, 3.0, -2.0])
    for motor, rbv in zip(halbach_controller.motors, initial_rbv, strict=True):
        set_mock_value(motor.user_readback, float(rbv))

    await halbach_controller.set(HalbachSetpoint(h_mt=50.0, field_angle_z_deg=-30.0))

    for motor, exp_pos in zip(halbach_controller.motors, lut_deg + 720.0, strict=True):
        cmd_pos = float(get_mock_put(motor.user_setpoint).call_args[0][0])
        assert cmd_pos == pytest.approx(exp_pos, abs=1e-4)


@pytest.mark.parametrize(
    ("step_mt", "step_deg", "start", "target", "expected_calls"),
    [
        (
            60.0,
            30.0,
            HalbachSetpoint(-170.0, 0.0),
            HalbachSetpoint(170.0, 0.0),
            6,
        ),
        (
            50.0,
            15.0,
            HalbachSetpoint(0.0, -45.0),
            HalbachSetpoint(0.0, 67.0),
            8,
        ),
    ],
)
async def test_waypoint_trajectory_executes_steps(
    halbach_controller: HalbachMagnetArrayController,
    step_mt: float,
    step_deg: float,
    start: HalbachSetpoint,
    target: HalbachSetpoint,
    expected_calls: int,
) -> None:
    await halbach_controller.set(start)
    for motor in halbach_controller.motors:
        get_mock_put(motor.user_setpoint).reset_mock()

    await halbach_controller.waypoint_step_mt.set(step_mt)
    await halbach_controller.waypoint_step_deg.set(step_deg)
    await halbach_controller.set(target)

    for motor in halbach_controller.motors:
        calls = get_mock_put(motor.user_setpoint).call_args_list
        assert len(calls) == expected_calls


def test_derived_signals_have_no_default_timeout(
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    assert halbach_controller.field._timeout is None
    assert halbach_controller.angle._timeout is None


async def test_failed_waypoint_keeps_last_completed_setpoint(
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    await halbach_controller.waypoint_step_mt.set(50.0)
    await halbach_controller.waypoint_step_deg.set(0.0)

    put_count = 0

    def fail_on_second_waypoint(pos: float, *_, **__) -> None:
        nonlocal put_count
        put_count += 1
        if put_count >= 2:
            raise RuntimeError("motor move aborted")
        set_mock_value(halbach_controller.m1.user_readback, float(pos))

    callback_on_mock_put(halbach_controller.m1.user_setpoint, fail_on_second_waypoint)

    with pytest.raises(RuntimeError, match="motor move aborted"):
        await halbach_controller.set(HalbachSetpoint(h_mt=150.0, field_angle_z_deg=0.0))

    assert await halbach_controller.get_current_field_and_angle() == pytest.approx(
        (50.0, 0.0)
    )


@pytest.mark.parametrize("fixed_angle_deg", [-90.0, -45.0, 0.0, 45.0, 90.0])
async def test_halbach_scan_across_zero_field_without_jumps(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    halbach_controller: HalbachMagnetArrayController,
    fixed_angle_deg: float,
) -> None:
    await halbach_controller.angle.set(fixed_angle_deg)
    for motor in halbach_controller.motors:
        get_mock_put(motor.user_setpoint).reset_mock()

    num_points = 19
    run_engine(scan([], halbach_controller.field, -170.0, 170.0, num=num_points))
    assert_emitted(
        run_engine_documents, start=1, descriptor=1, event=num_points, stop=1
    )

    trajectories = np.array(
        [
            [c.args[0] for c in get_mock_put(m.user_setpoint).call_args_list]
            for m in halbach_controller.motors
        ]
    )
    assert trajectories.shape == (4, num_points)
    assert float(np.max(np.abs(np.diff(trajectories, axis=1)))) < 90.0


@pytest.mark.parametrize("fixed_h_mt", [-170.0, -90.0, 90.0, 170.0])
async def test_halbach_angle_sweep_without_jumps(
    run_engine: RunEngine,
    halbach_controller: HalbachMagnetArrayController,
    fixed_h_mt: float,
) -> None:
    await halbach_controller.field.set(fixed_h_mt)
    for motor in halbach_controller.motors:
        get_mock_put(motor.user_setpoint).reset_mock()

    num_points = 12
    run_engine(scan([], halbach_controller.angle, -110.0, 110.0, num=num_points))

    trajectories = np.array(
        [
            [c.args[0] for c in get_mock_put(m.user_setpoint).call_args_list]
            for m in halbach_controller.motors
        ]
    )
    assert trajectories.shape == (4, num_points)
    assert float(np.max(np.abs(np.diff(trajectories, axis=1)))) < 90.0


async def test_halbach_2d_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    halbach_controller: HalbachMagnetArrayController,
) -> None:
    run_engine(
        grid_scan(
            [],
            halbach_controller.field,
            -100.0,
            100.0,
            3,
            halbach_controller.angle,
            -45.0,
            45.0,
            3,
        )
    )
    assert_emitted(run_engine_documents, start=1, descriptor=1, event=9, stop=1)
