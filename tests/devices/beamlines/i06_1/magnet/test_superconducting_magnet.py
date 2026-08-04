import asyncio
import math
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from bluesky import FailedStatus, RunEngine
from bluesky.plan_stubs import mv
from bluesky.protocols import Reading
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnet import (
    FlyVectorMagnetInfo,
    MagnetAxis,
    MagnetLimitStatus,
    MagnetMode,
    MagnetPosition,
    MagnetPositionError,
    MagnetRampStatus,
    MagnetRequest,
    MagnetSphericalPosition,
    SuperConductingMagnet,
    SuperConductingMagnetController,
    movement,
)
from dodal.devices.beamlines.i06_1.magnet.movement import MovementStrategy
from tests.devices.beamlines.i06_1.magnet.utils import (
    EXPECTED_CARTESIAN_SPHERICAL_CONVERSION,
)


@pytest.fixture
def scmc() -> SuperConductingMagnetController:
    with init_devices(mock=True):
        scmc = SuperConductingMagnetController("TEST:")
    return scmc


@pytest.fixture
def scm(scmc: SuperConductingMagnetController) -> SuperConductingMagnet:
    with init_devices(mock=True):
        scm = SuperConductingMagnet(scmc)
    return scm


async def test_scm_read(scm: SuperConductingMagnet) -> None:

    await assert_reading(
        scm,
        {
            "scm-cart-x": partial_reading(0),
            "scm-cart-y": partial_reading(0),
            "scm-cart-z": partial_reading(0),
            "scm-sph-theta": partial_reading(0),
            "scm-sph-rho": partial_reading(0),
            "scm-sph-phi": partial_reading(0),
        },
    )


async def test_scmc_configuration(scm: SuperConductingMagnet) -> None:
    await assert_configuration(
        scm, {"scm-controller-mode": partial_reading(MagnetMode.UNIAXIAL_X)}
    )


@pytest.mark.parametrize(
    "axis, value, expected_x, expected_y, expected_z",
    [
        ("x", 0.1, 0.1, 0, 0),
        ("y", 0.5, 0, 0.5, 0),
        ("z", 0.2, 0, 0, 0.2),
    ],
)
async def test_scmc_axis_set_uses_correct_axis(
    scm: SuperConductingMagnet,
    axis: str,
    value: float,
    expected_x: float,
    expected_y: float,
    expected_z: float,
) -> None:
    await scm.controller.mode.set(getattr(MagnetMode, "UNIAXIAL_" + axis.capitalize()))
    await getattr(scm.cart, axis).set(value)
    x, y, z = await asyncio.gather(
        scm.cart.x.get_value(),
        scm.cart.y.get_value(),
        scm.cart.z.get_value(),
    )
    assert x == expected_x
    assert y == expected_y
    assert z == expected_z


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
async def test_scmc_sph_set_using_spherical(
    scm: SuperConductingMagnet,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scm.controller.mode.set(MagnetMode.SPHERICAL)
    await scm.sph.set(spherical.to_request_pos())
    rho, theta, phi = await asyncio.gather(
        scm.sph.rho.get_value(),
        scm.sph.theta.get_value(),
        scm.sph.phi.get_value(),
    )
    assert rho == pytest.approx(spherical.rho)
    assert theta == pytest.approx(spherical.theta)
    assert phi == pytest.approx(spherical.phi)

    x, y, z = await asyncio.gather(
        scm.cart.x.get_value(),
        scm.cart.y.get_value(),
        scm.cart.z.get_value(),
    )
    assert x == pytest.approx(cartesian.x)
    assert y == pytest.approx(cartesian.y)
    assert z == pytest.approx(cartesian.z)


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
async def test_scmc_cart_set_using_cartesian(
    scm: SuperConductingMagnet,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scm.controller.mode.set(MagnetMode.CUBIC)
    await scm.cart.set(cartesian.to_request_pos())
    x, y, z = await asyncio.gather(
        scm.cart.x.get_value(),
        scm.cart.y.get_value(),
        scm.cart.z.get_value(),
    )
    assert x == pytest.approx(cartesian.x)
    assert y == pytest.approx(cartesian.y)
    assert z == pytest.approx(cartesian.z)

    rho, theta, phi = await asyncio.gather(
        scm.sph.rho.get_value(),
        scm.sph.theta.get_value(),
        scm.sph.phi.get_value(),
    )
    assert rho == pytest.approx(spherical.rho)
    assert theta == pytest.approx(spherical.theta)
    assert phi == pytest.approx(spherical.phi)


@pytest.mark.parametrize(
    "axes, values, expected_rho, expected_phi, expected_theta, expected_x, expected_y, expected_z",
    [
        (("rho",), (1,), 1, 0, 0, 0, 1, 0),
        (("rho", "phi"), (1, 90), 1, 90, 0, 0, 0, 1),
        (("rho", "phi", "theta"), (1, 45, 45), 1, 45, 45, -0.5, math.sqrt(2) / 2, 0.5),
    ],
)
async def test_scmc_spherical_individual_axis_set(
    scm: SuperConductingMagnet,
    axes: tuple[str],
    values: tuple[float],
    expected_rho: float,
    expected_phi: float,
    expected_theta: float,
    expected_x: float,
    expected_y: float,
    expected_z: float,
) -> None:
    await scm.controller.mode.set(MagnetMode.SPHERICAL)
    for axis, value in zip(axes, values, strict=True):
        await getattr(scm.sph, axis).set(value)

    await assert_reading(
        scm,
        {
            "scm-cart-x": partial_reading(expected_x),
            "scm-cart-y": partial_reading(expected_y),
            "scm-cart-z": partial_reading(expected_z),
            "scm-sph-rho": partial_reading(expected_rho),
            "scm-sph-phi": partial_reading(expected_phi),
            "scm-sph-theta": partial_reading(expected_theta),
        },
    )


async def test_scmc_raises_error_if_limit_status_is_violation(
    scm: SuperConductingMagnet,
) -> None:
    await scm.mode.set(MagnetMode.UNIAXIAL_X)
    set_mock_value(scm.controller.limit_status, MagnetLimitStatus.VIOLATION)
    with pytest.raises(MagnetPositionError):
        await scm.cart.x.set(1)


@pytest.mark.parametrize(
    "mode", [MagnetMode.UNIAXIAL_X, MagnetMode.UNIAXIAL_Y, MagnetMode.UNIAXIAL_Z]
)
async def test_scmc_axis_with_ramp_rate_wired_correctly_with_prepare(
    scm: SuperConductingMagnet,
    mode: MagnetMode,
) -> None:
    await scm.controller.mode.set(mode)
    magnet_axis: MagnetAxis = getattr(scm.controller, mode.axis_alias)

    fly_info = FlyVectorMagnetInfo(
        fly_axis=mode.axis_alias, start_position=0.2, end_position=1.2, ramp_rate=0.25
    )
    await scm.prepare(fly_info)
    assert await magnet_axis.demand.get_value() == fly_info.start_position
    assert await magnet_axis.ramp_rate.get_value() == fly_info.ramp_rate


async def test_scmc_axis_kickoff_and_complete(
    scm: SuperConductingMagnet,
) -> None:
    await scm.mode.set(MagnetMode.UNIAXIAL_X)
    fly_info = FlyVectorMagnetInfo(
        fly_axis=MagnetMode.UNIAXIAL_X.axis_alias,
        start_position=1,
        end_position=2,
        ramp_rate=0.5,
    )
    assert scm.controller._fly_info is None
    await scm.prepare(fly_info)
    assert scm.controller._fly_info is fly_info
    assert scm.controller._fly_status is None
    await scm.kickoff()
    assert scm.controller._fly_info is None
    await scm.complete()
    assert await scm.cart.x.get_value() == fly_info.end_position


async def test_scmc_axis_kickoff_and_complete_raises_error_without_prepare(
    scm: SuperConductingMagnet,
):
    await scm.mode.set(MagnetMode.UNIAXIAL_X)
    # Do multiple times to make sure you cannot kickoff or complete without preparing
    # each time
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await scm.kickoff()
        with pytest.raises(RuntimeError):
            await scm.complete()

        fly_info = FlyVectorMagnetInfo(
            fly_axis=MagnetMode.UNIAXIAL_X.axis_alias,
            start_position=1,
            end_position=2,
            ramp_rate=0.5,
        )
        await scm.prepare(fly_info)
        await scm.kickoff()
        await scm.complete()


async def test_scmc_mock_device_behaviour(
    scm: SuperConductingMagnet,
) -> None:
    assert await scm.controller.limit_status.get_value() == MagnetLimitStatus.OK

    set_mock_value(scm.controller.x.demand, 1)
    set_mock_value(scm.controller.y.demand, 1)
    set_mock_value(scm.controller.z.demand, 1)

    ramp_states: list[MagnetRampStatus] = []

    def _ramp_state_callback(value: dict[str, Reading[MagnetRampStatus]]):
        ramp_states.append(value[scm.controller.ramp_status.name]["value"])

    scm.controller.ramp_status.subscribe_reading(_ramp_state_callback)

    # Set a mode value and check to see if all values are set back to zero and ramp
    # status change happened
    await scm.mode.set(MagnetMode.UNIAXIAL_X)

    x_d, y_d, z_d, x_rbv, y_rbv, z_rbv = await asyncio.gather(
        scm.controller.x.demand.get_value(),
        scm.controller.y.demand.get_value(),
        scm.controller.z.demand.get_value(),
        scm.cart.x.get_value(),
        scm.cart.y.get_value(),
        scm.cart.z.get_value(),
    )
    assert x_d == y_d == z_d == x_rbv == y_rbv == z_rbv == 0
    assert ramp_states == [
        MagnetRampStatus.RAMP_MADE,
        MagnetRampStatus.RAMPING,
        MagnetRampStatus.RAMP_MADE,
    ]


async def test_scmc_no_movement_strategy_for_mode(
    scm: SuperConductingMagnet,
) -> None:
    mode = await scm.controller.mode.get_value()
    with patch.dict(scm.controller._MODE_MOVEMENT_STRATEGY, {}, clear=True):
        with pytest.raises(
            ValueError,
            match=f"No movement strategy has been configured for device scm-controller for mode {mode}",
        ):
            await scm.cart.x.set(5)


@pytest.mark.parametrize(
    "mode, expected",
    [
        (MagnetMode.SPHERICAL, movement.SphericalMovement),
        (MagnetMode.CUBIC, movement.CubicMovement),
        (MagnetMode.PLANAR_XZ, movement.PlanarXZMovement),
        (MagnetMode.QUADRANT_XY, movement.QuadrantXYMovement),
        (MagnetMode.UNIAXIAL_X, movement.UniaxialMovement),
        (MagnetMode.UNIAXIAL_Y, movement.UniaxialMovement),
        (MagnetMode.UNIAXIAL_Z, movement.UniaxialMovement),
    ],
)
async def test_scmc_magnet_mode_to_movement_strategy_configuration(
    scm: SuperConductingMagnet,
    mode: MagnetMode,
    expected: type[movement.MovementStrategy],
) -> None:
    assert isinstance(scm.controller._MODE_MOVEMENT_STRATEGY[mode], expected)


async def test_scmc_magnet_mode_to_uniaxial_movement_strategy_configuration(
    scm: SuperConductingMagnet,
) -> None:
    assert (
        scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_X].mode  # type:ignore
        == MagnetMode.UNIAXIAL_X
    )
    assert (
        scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_Y].mode  # type:ignore
        == MagnetMode.UNIAXIAL_Y
    )
    assert (
        scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_Z].mode  # type:ignore
        == MagnetMode.UNIAXIAL_Z
    )


async def test_scmc_executes_movement_stragey_and_ramp_at_each_step(
    scm: SuperConductingMagnet,
) -> None:

    movement_strategy = MagicMock()

    mov_str_return_values = [
        movement.MagnetRequest(z=2),
        movement.MagnetRequest(x=1, y=2, z=3),
    ]
    expected_apply_step_calls = [
        call(mov_str_return_values[0], timeout=ANY),
        call(mov_str_return_values[1], timeout=ANY),
    ]
    movement_strategy.move_steps.return_value = mov_str_return_values

    scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_X] = movement_strategy

    scm.controller._trigger_ramp = AsyncMock()

    with patch(
        "dodal.devices.beamlines.i06_1.magnet.superconducting_magnet.SuperConductingMagnetController._apply_step",
        wraps=scm.controller._apply_step,
    ) as mock_apply_step:
        await scm.mode.set(MagnetMode.UNIAXIAL_X)
        await scm.cart.x.set(4)

        assert mock_apply_step.call_args_list == expected_apply_step_calls
        assert scm.controller._trigger_ramp.call_count == len(mov_str_return_values)


async def test_external_parallel_moves_for_scmc_raise_error(
    scm: SuperConductingMagnet, run_engine: RunEngine
) -> None:
    run_engine(mv(scm.mode, MagnetMode.CUBIC))
    # Coordinated parallel move of axes submitted together is okay.
    run_engine(mv(scm.cart, MagnetPosition(x=1, y=1, z=1)))

    # Coordinated parallel move on axes done separately fails.
    with pytest.raises(FailedStatus):
        run_engine(mv(scm.cart.x, 0.5, scm.cart.y, 0.5))

    # Check after a blocked move and the first move finished, we can still do another move.
    run_engine(mv(scm.cart, MagnetPosition(x=0.1, y=0.2, z=0.3)))


async def test_scmc_set_within_boundary_checks_each_movement_step(
    scm: SuperConductingMagnet,
) -> None:
    movement_strategy = MagicMock(spec=MovementStrategy)
    initial_position = MagnetPosition(x=0, y=0, z=0)
    position_after_step_1 = MagnetPosition(x=0, y=1, z=0)
    position_after_step_2 = MagnetPosition(x=1, y=1, z=0)

    target = MagnetRequest(x=1, y=1)

    steps = [MagnetRequest(y=1), MagnetRequest(x=1)]
    movement_strategy.move_steps.return_value = steps

    scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.QUADRANT_XY] = movement_strategy

    scm.controller.get_readback_position = AsyncMock(
        side_effect=[
            initial_position,
            position_after_step_1,
            position_after_step_2,
        ]
    )
    filed_limit = await scm.controller.get_field_limit()
    scm.controller.mode.get_value = AsyncMock(return_value=MagnetMode.QUADRANT_XY)
    scm.controller._apply_step = AsyncMock()

    await scm.controller.set_within_boundary(target)

    assert movement_strategy.check_within_limits.call_args_list == [
        call(initial_position, target, filed_limit),
        call(initial_position, steps[0], filed_limit),
        call(position_after_step_1, steps[1], filed_limit),
    ]
    assert scm.controller._apply_step.call_args_list == [
        call(steps[0], timeout=ANY),
        call(steps[1], timeout=ANY),
    ]
    assert scm.controller.get_readback_position.call_count == 3


@pytest.mark.asyncio
async def test_scmc_set_within_boundary_stops_when_step_is_outside_limits(
    scm: SuperConductingMagnet,
) -> None:
    movement_strategy = MagicMock(spec=MovementStrategy)
    initial_position = MagnetPosition(x=0, y=0, z=0)
    target = MagnetRequest(x=1, y=1)
    steps = [MagnetRequest(y=1), MagnetRequest(x=1)]

    movement_strategy.move_steps.return_value = steps
    movement_strategy.check_within_limits.side_effect = [
        None,  # Final target is valid.
        None,  # First step is valid.
        MagnetPositionError.axis_below_limit(MagnetMode.QUADRANT_XY, 0, -1, "x"),
    ]
    scm.controller._MODE_MOVEMENT_STRATEGY[MagnetMode.QUADRANT_XY] = movement_strategy
    scm.controller.get_readback_position = AsyncMock(
        side_effect=[initial_position, MagnetPosition(x=0, y=1, z=0)]
    )
    scm.controller.mode.get_value = AsyncMock(return_value=MagnetMode.QUADRANT_XY)
    scm.controller._apply_step = AsyncMock()

    with pytest.raises(MagnetPositionError):
        await scm.controller.set_within_boundary(target)
    # The invalid second step must never be applied.
    scm.controller._apply_step.assert_awaited_once_with(steps[0], timeout=ANY)


@pytest.mark.asyncio
async def test_prepare_raises_when_no_movement_strategy(
    scm: SuperConductingMagnet,
):

    original_strategies = dict(scm.controller._MODE_MOVEMENT_STRATEGY)
    scm.controller._MODE_MOVEMENT_STRATEGY.clear()

    fly_info = FlyVectorMagnetInfo(
        fly_axis=MagnetMode.UNIAXIAL_X.axis_alias,
        start_position=1,
        end_position=2,
        ramp_rate=0.5,
    )
    with pytest.raises(
        ValueError,
        match="No movement strategy has been configured for device",
    ):
        await scm.prepare(fly_info)
    scm.controller._MODE_MOVEMENT_STRATEGY.update(original_strategies)


async def test_prepare_raises_on_invalid_ramp_rate(
    scm: SuperConductingMagnet,
):
    invalid_ramp_rate = 15.0
    await scm.mode.set(MagnetMode.UNIAXIAL_X)
    fly_info = FlyVectorMagnetInfo(
        fly_axis="x",
        start_position=1,
        end_position=2,
        ramp_rate=invalid_ramp_rate,
    )

    with pytest.raises(
        ValueError,
        match="Requested ramp rate",
    ):
        await scm.prepare(fly_info)


@pytest.mark.parametrize(
    "mode",
    [
        (MagnetMode.SPHERICAL),
        (MagnetMode.PLANAR_XZ),
        (MagnetMode.QUADRANT_XY),
    ],
)
async def test_prepare_raises_on_invalid_mode(
    scm: SuperConductingMagnet, mode: MagnetMode
):
    await scm.mode.set(mode)
    fly_info = FlyVectorMagnetInfo(
        fly_axis="Y",
        start_position=1,
        end_position=2,
        ramp_rate=0.2,
    )

    with pytest.raises(
        ValueError,
        match="Only uniaxial and cubic modes are supported",
    ):
        await scm.prepare(fly_info)
