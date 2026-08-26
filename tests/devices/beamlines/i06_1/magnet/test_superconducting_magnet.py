import asyncio
import math
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from bluesky import FailedStatus, RunEngine
from bluesky.plan_stubs import mv
from bluesky.protocols import Reading
from ophyd_async.core import DEFAULT_TIMEOUT, SignalR, init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnet import (
    FlyMagnetInfo,
    MagnetAxis,
    MagnetAxisRampRateController,
    MagnetLimitStatus,
    MagnetMode,
    MagnetPosition,
    MagnetPositionError,
    MagnetRampStatus,
    MagnetRequest,
    MagnetSphericalPosition,
    MockSuperConductingMagnetController,
    SuperConductingMagnetController,
    ThreeMagnetAxisPowerSupply,
    movement,
)
from dodal.devices.beamlines.i06_1.magnet.movement import MovementStrategy
from tests.devices.beamlines.i06_1.magnet.utils import (
    EXPECTED_CARTESIAN_SPHERICAL_CONVERSION,
)


@pytest.fixture
def scmc_psu() -> ThreeMagnetAxisPowerSupply:
    with init_devices(mock=True):
        scmc_psu = ThreeMagnetAxisPowerSupply("TEST:")
    return scmc_psu


@pytest.fixture
async def scmc(
    scmc_psu: ThreeMagnetAxisPowerSupply,
) -> SuperConductingMagnetController:
    # Optimise tests by making movement of readback to setpoint instant.
    scmc = SuperConductingMagnetController("TEST:", scmc_psu, name="scmc")
    await scmc.connect(mock=MockSuperConductingMagnetController(steps=0))
    return scmc


async def test_scmc_read(scmc: SuperConductingMagnetController) -> None:
    await assert_reading(
        scmc,
        {
            "scmc-cart-x": partial_reading(0),
            "scmc-cart-y": partial_reading(0),
            "scmc-cart-z": partial_reading(0),
            "scmc-sph-theta": partial_reading(0),
            "scmc-sph-rho": partial_reading(0),
            "scmc-sph-phi": partial_reading(0),
        },
    )


async def test_scmc_configuration(scmc: SuperConductingMagnetController) -> None:
    await assert_configuration(
        scmc, {"scmc-mode": partial_reading(MagnetMode.UNIAXIAL_X)}
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
    scmc: SuperConductingMagnetController,
    axis: str,
    value: float,
    expected_x: float,
    expected_y: float,
    expected_z: float,
) -> None:
    await scmc.mode.set(getattr(MagnetMode, "UNIAXIAL_" + axis.capitalize()))
    await getattr(scmc.cart, axis).set(value)
    x, y, z = await asyncio.gather(
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x == expected_x
    assert y == expected_y
    assert z == expected_z


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
async def test_scmc_sph_set_using_spherical(
    scmc: SuperConductingMagnetController,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scmc.mode.set(MagnetMode.SPHERICAL)
    await scmc.sph.set(spherical.to_request_pos())
    rho, theta, phi = await asyncio.gather(
        scmc.sph.rho.get_value(),
        scmc.sph.theta.get_value(),
        scmc.sph.phi.get_value(),
    )
    assert rho == pytest.approx(spherical.rho)
    assert theta == pytest.approx(spherical.theta)
    assert phi == pytest.approx(spherical.phi)

    x, y, z = await asyncio.gather(
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x == pytest.approx(cartesian.x)
    assert y == pytest.approx(cartesian.y)
    assert z == pytest.approx(cartesian.z)


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
async def test_scmc_cart_set_using_cartesian(
    scmc: SuperConductingMagnetController,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scmc.mode.set(MagnetMode.CUBIC)
    await scmc.cart.set(cartesian.to_request_pos())
    x, y, z = await asyncio.gather(
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x == pytest.approx(cartesian.x)
    assert y == pytest.approx(cartesian.y)
    assert z == pytest.approx(cartesian.z)

    rho, theta, phi = await asyncio.gather(
        scmc.sph.rho.get_value(),
        scmc.sph.theta.get_value(),
        scmc.sph.phi.get_value(),
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
    scmc: SuperConductingMagnetController,
    axes: tuple[str],
    values: tuple[float],
    expected_rho: float,
    expected_phi: float,
    expected_theta: float,
    expected_x: float,
    expected_y: float,
    expected_z: float,
) -> None:
    await scmc.mode.set(MagnetMode.SPHERICAL)
    for axis, value in zip(axes, values, strict=True):
        await getattr(scmc.sph, axis).set(value)

    await assert_reading(
        scmc,
        {
            "scmc-cart-x": partial_reading(expected_x),
            "scmc-cart-y": partial_reading(expected_y),
            "scmc-cart-z": partial_reading(expected_z),
            "scmc-sph-rho": partial_reading(expected_rho),
            "scmc-sph-phi": partial_reading(expected_phi),
            "scmc-sph-theta": partial_reading(expected_theta),
        },
    )


async def test_scmc_raises_error_if_limit_status_is_violation(
    scmc: SuperConductingMagnetController,
) -> None:
    await scmc.mode.set(MagnetMode.UNIAXIAL_X)
    set_mock_value(scmc.limit_status, MagnetLimitStatus.VIOLATION)
    with pytest.raises(MagnetPositionError):
        await scmc.cart.x.set(1)


@pytest.mark.parametrize(
    "mode", [MagnetMode.UNIAXIAL_X, MagnetMode.UNIAXIAL_Y, MagnetMode.UNIAXIAL_Z]
)
async def test_scmc_axis_with_ramp_rate_wired_correctly_with_prepare(
    scmc: SuperConductingMagnetController,
    scmc_psu: ThreeMagnetAxisPowerSupply,
    mode: MagnetMode,
) -> None:
    await scmc.mode.set(mode)
    magnet_axis: MagnetAxis = getattr(scmc.cart, mode.axis_alias)
    ramp_axis: MagnetAxisRampRateController = getattr(
        scmc_psu, mode.axis_alias
    ).ramp_rate

    fly_info = FlyMagnetInfo(start_position=1, end_position=6, ramp_rate=1.5)
    await magnet_axis.prepare(fly_info)
    assert await magnet_axis.demand.get_value() == fly_info.start_position
    assert await ramp_axis.demand.get_value() == fly_info.ramp_rate


async def test_scmc_axis_kickoff_and_complete(
    scmc: SuperConductingMagnetController,
) -> None:
    await scmc.mode.set(MagnetMode.UNIAXIAL_X)
    fly_info = FlyMagnetInfo(start_position=1, end_position=2, ramp_rate=2)
    assert scmc.cart.x._fly_info is None
    await scmc.cart.x.prepare(fly_info)
    assert scmc.cart.x._fly_info is fly_info
    assert scmc.cart.x._fly_status is None
    await scmc.cart.x.kickoff()
    assert scmc.cart.x._fly_info is None
    await scmc.cart.x.complete()
    assert await scmc.cart.x.readback.get_value() == fly_info.end_position


async def test_scmc_axis_kickoff_and_complete_raises_error_without_prepare(
    scmc: SuperConductingMagnetController,
):
    await scmc.mode.set(MagnetMode.UNIAXIAL_X)
    # Do multiple times to make sure you cannot kickoff or complete without preparing
    # each time
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await scmc.cart.x.kickoff()

        with pytest.raises(RuntimeError):
            await scmc.cart.x.complete()

        fly_info = FlyMagnetInfo(start_position=1, end_position=2, ramp_rate=1)
        await scmc.cart.x.prepare(fly_info)
        await scmc.cart.x.kickoff()
        await scmc.cart.x.complete()


async def test_scmc_mock_device_behaviour(
    scmc: SuperConductingMagnetController,
) -> None:
    assert await scmc.limit_status.get_value() == MagnetLimitStatus.OK

    set_mock_value(scmc.cart.x.demand, 1)
    set_mock_value(scmc.cart.y.demand, 1)
    set_mock_value(scmc.cart.z.demand, 1)

    ramp_states: list[MagnetRampStatus] = []

    def _ramp_state_callback(value: dict[str, Reading[MagnetRampStatus]]):
        ramp_states.append(value[scmc.ramp_status.name]["value"])

    scmc.ramp_status.subscribe_reading(_ramp_state_callback)

    # Set a mode value and check to see if all values are set back to zero and ramp
    # status change happened
    await scmc.mode.set(MagnetMode.UNIAXIAL_X)

    x_d, y_d, z_d, x_rbv, y_rbv, z_rbv = await asyncio.gather(
        scmc.cart.x.demand.get_value(),
        scmc.cart.y.demand.get_value(),
        scmc.cart.z.demand.get_value(),
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x_d == y_d == z_d == x_rbv == y_rbv == z_rbv == 0
    assert ramp_states == [
        MagnetRampStatus.RAMP_MADE,
        MagnetRampStatus.RAMPING,
        MagnetRampStatus.RAMP_MADE,
    ]


async def test_scmc_no_movement_strategy_for_mode(
    scmc: SuperConductingMagnetController,
) -> None:
    mode = await scmc.mode.get_value()
    with patch.dict(scmc._MODE_MOVEMENT_STRATEGY, {}, clear=True):
        with pytest.raises(
            ValueError,
            match=f"No movement strategy has been configured for device scmc for mode {mode}",
        ):
            await scmc.cart.x.set(5)


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
    scmc: SuperConductingMagnetController,
    mode: MagnetMode,
    expected: type[movement.MovementStrategy],
) -> None:
    assert isinstance(scmc._MODE_MOVEMENT_STRATEGY[mode], expected)


async def test_scmc_magnet_mode_to_uniaxial_movement_strategy_configuration(
    scmc: SuperConductingMagnetController,
) -> None:
    assert (
        scmc._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_X].mode  # type:ignore
        == MagnetMode.UNIAXIAL_X
    )
    assert (
        scmc._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_Y].mode  # type:ignore
        == MagnetMode.UNIAXIAL_Y
    )
    assert (
        scmc._MODE_MOVEMENT_STRATEGY[MagnetMode.UNIAXIAL_Z].mode  # type:ignore
        == MagnetMode.UNIAXIAL_Z
    )


async def test_scmc_executes_movement_strategy_and_ramp_at_each_step(
    scmc: SuperConductingMagnetController,
) -> None:
    movement_strategy = MagicMock()

    move_steps = [
        movement.MagnetRequest(x=0.5),
        movement.MagnetRequest(x=1.2),
    ]
    movement_strategy.move_steps.return_value = move_steps

    expected_apply_step_calls = [
        call(movement.MagnetRequest(x=0.5), timeout=DEFAULT_TIMEOUT),
        call(movement.MagnetRequest(x=1.2), timeout=DEFAULT_TIMEOUT),
    ]
    with patch.dict(
        scmc._MODE_MOVEMENT_STRATEGY,
        {MagnetMode.UNIAXIAL_X: movement_strategy},
    ):
        scmc._trigger_ramp = AsyncMock()

        with patch.object(
            scmc,
            "_apply_step",
            wraps=scmc._apply_step,
        ) as mock_apply_step:
            # Configures PSU limits to X=2, Y=0, Z=0
            await scmc.mode.set(MagnetMode.UNIAXIAL_X)

            # Target is within the X axis limit
            await scmc.cart.x.set(1.2)

        movement_strategy.move_steps.assert_called_once_with(
            ANY,
            movement.MagnetRequest(x=1.2),
        )

        assert mock_apply_step.call_args_list == expected_apply_step_calls
        assert scmc._trigger_ramp.call_count == len(move_steps)


async def test_external_parallel_moves_for_scmc_raise_error(
    scmc: SuperConductingMagnetController, run_engine: RunEngine
) -> None:
    run_engine(mv(scmc.mode, MagnetMode.CUBIC))
    # Coordinated parallel move of axes submitted together is okay.
    run_engine(mv(scmc.cart, MagnetPosition(x=1, y=1, z=1)))

    # Coordinated parallel move on axes done separately fails.
    with pytest.raises(FailedStatus):
        run_engine(mv(scmc.cart.x, 0.5, scmc.cart.y, 0.5))

    # Check after a blocked move and the first move finished, we can still do another move.
    run_engine(mv(scmc.cart, MagnetPosition(x=0.1, y=0.2, z=0.3)))


async def test_scmc_set_within_boundary_checks_each_movement_step(
    scmc: SuperConductingMagnetController,
) -> None:
    movement_strategy = MagicMock(spec=MovementStrategy)
    initial_position = MagnetPosition(x=0, y=0, z=0)
    position_after_step_1 = MagnetPosition(x=0, y=1, z=0)
    position_after_step_2 = MagnetPosition(x=1, y=1, z=0)

    target = MagnetRequest(x=1, y=1)

    steps = [MagnetRequest(y=1), MagnetRequest(x=1)]
    movement_strategy.move_steps.return_value = steps

    scmc._MODE_MOVEMENT_STRATEGY[MagnetMode.QUADRANT_XY] = movement_strategy

    scmc.cart.get_readback_position = AsyncMock(
        side_effect=[
            initial_position,
            position_after_step_1,
            position_after_step_2,
        ]
    )
    # Use actual set so it callbacks to the mock limits
    await scmc.mode.set(MagnetMode.QUADRANT_XY)
    scmc._apply_step = AsyncMock()

    await scmc.set_within_boundary(target)

    assert movement_strategy.check_within_limits.call_args_list == [
        call(
            initial_position,
            target,
        ),
        call(initial_position, steps[0]),
        call(position_after_step_1, steps[1]),
    ]
    assert scmc._apply_step.call_args_list == [
        call(steps[0], timeout=DEFAULT_TIMEOUT),
        call(steps[1], timeout=DEFAULT_TIMEOUT),
    ]
    assert scmc.cart.get_readback_position.call_count == 3


@pytest.mark.asyncio
async def test_scmc_set_within_boundary_stops_when_step_is_outside_limits(
    scmc: SuperConductingMagnetController,
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
    scmc._MODE_MOVEMENT_STRATEGY[MagnetMode.QUADRANT_XY] = movement_strategy
    scmc.cart.get_readback_position = AsyncMock(
        side_effect=[initial_position, MagnetPosition(x=0, y=1, z=0)]
    )
    # Use actual set so it callbacks to the mock limits
    await scmc.mode.set(MagnetMode.QUADRANT_XY)
    scmc._apply_step = AsyncMock()

    with pytest.raises(MagnetPositionError):
        await scmc.set_within_boundary(target)
    # The invalid second step must never be applied.
    scmc._apply_step.assert_awaited_once_with(steps[0], timeout=DEFAULT_TIMEOUT)


@pytest.mark.parametrize(
    "mode, expected_limits",
    [
        (MagnetMode.UNIAXIAL_X, (2, 0, 0)),
        (MagnetMode.UNIAXIAL_Y, (0, 2, 0)),
        (MagnetMode.UNIAXIAL_Z, (0, 0, 6)),
        (MagnetMode.CUBIC, (2, 2, 2)),
        (MagnetMode.QUADRANT_XY, (2, 2, 2)),
        (MagnetMode.PLANAR_XZ, (2, 0, 2)),
        (MagnetMode.SPHERICAL, (2, 2, 2)),
    ],
)
async def test_scmc_mock_axis_limits_are_correct(
    scmc: SuperConductingMagnetController,
    mode: MagnetMode,
    expected_limits: tuple[float, float, float],
):
    await scmc.mode.set(mode)
    limits = await asyncio.gather(
        scmc.psu_ref().x.limit.get_value(),
        scmc.psu_ref().y.limit.get_value(),
        scmc.psu_ref().z.limit.get_value(),
    )
    assert limits == list(expected_limits)


@pytest.mark.parametrize(
    "start_pos, ramp_rates, target_request, expected_max_time",
    [
        (
            (1.0, 0.0, -1.0),
            (1.0, 0.75, 0.5),
            MagnetRequest(x=1.5, y=1.5, z=1.0),
            4.0,
        ),
        (
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
            MagnetRequest(x=1.5, y=1.5, z=0.0),
            1.5,
        ),
        (
            (0.0, 1.0, -1.0),
            (1.0, 1.0, 1.0),
            MagnetRequest(x=1.5, y=1.0, z=1.5),
            2.5,
        ),
        (
            (0.0, 0.0, -1.5),
            (2.0, 2.0, 2.0),
            MagnetRequest(x=None, y=None, z=1.5),
            1.5,
        ),
    ],
)
async def test_scmc_set_within_boundary_timeout_set_correctly(
    scmc: SuperConductingMagnetController,
    start_pos: tuple[float, float, float],
    ramp_rates: tuple[float, float, float],
    target_request: MagnetRequest,
    expected_max_time: float,
) -> None:
    set_mock_value(scmc.mode, MagnetMode.CUBIC)

    start_x, start_y, start_z = start_pos
    set_mock_value(scmc.cart.x.readback, start_x)
    set_mock_value(scmc.cart.y.readback, start_y)
    set_mock_value(scmc.cart.z.readback, start_z)

    scmc.psu_ref().get_ramp_rate = AsyncMock(return_value=ramp_rates)
    scmc.psu_ref().check_axes_within_limit = AsyncMock()

    expected_timeout = expected_max_time + DEFAULT_TIMEOUT

    with patch.object(scmc, "_apply_step", wraps=scmc._apply_step) as mock_apply_step:
        await scmc.set_within_boundary(target_request)
        mock_apply_step.assert_called_once_with(
            target_request,
            timeout=expected_timeout,
        )


@pytest.mark.parametrize(
    "steps, ramp_time",
    [
        pytest.param(0, 0.0, id="instant"),
        pytest.param(4, 0.04, id="stepped"),
    ],
)
@pytest.mark.parametrize(
    "axis, mode, value",
    [
        pytest.param("x", MagnetMode.UNIAXIAL_X, 1.0, id="x"),
        pytest.param("y", MagnetMode.UNIAXIAL_Y, 1.0, id="y"),
        pytest.param("z", MagnetMode.UNIAXIAL_Z, 1.0, id="z"),
    ],
)
async def test_mock_scmc_only_ramps_target_axis(
    scmc_psu: ThreeMagnetAxisPowerSupply,
    steps: int,
    ramp_time: float,
    axis: str,
    mode: MagnetMode,
    value: float,
):
    scmc = SuperConductingMagnetController("PV:", scmc_psu, name="scmc")
    await scmc.connect(
        mock=MockSuperConductingMagnetController(
            steps=steps,
            ramp_time=ramp_time,
        )
    )
    await scmc.mode.set(mode)

    readbacks: dict[str, SignalR[float]] = {
        axis: getattr(scmc.cart, axis).readback for axis in ("x", "y", "z")
    }
    values: dict[str, list[float]] = {axis: [] for axis in readbacks}

    for axis_name, readback in readbacks.items():
        readback_name = readback.name
        readback.subscribe(
            lambda value, axis_name=axis_name, readback_name=readback_name: values[
                axis_name
            ].append(value[readback_name]["value"])
        )
    await getattr(scmc.cart, axis).set(value)
    # The initial 0.0 is emitted when the readback subscription is created,
    # followed by each value produced during the ramp.
    assert values[axis] == [
        0.0,
        *(value * step / max(steps, 1) for step in range(1, max(steps, 1) + 1)),
    ]
    # Non-target axes should only emit their initial readback value and should not
    # be updated by the ramp as value not changed.
    for other_axis in readbacks:
        if other_axis != axis:
            assert values[other_axis] == [0.0]
