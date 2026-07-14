import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from bluesky.protocols import Reading
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnets import (
    FlyMagnetInfo,
    MagnetAxis,
    MagnetAxisRampRateController,
    MagnetLimitStatus,
    MagnetModes,
    MagnetPosition,
    MagnetPositionError,
    MagnetRampStatus,
    MagnetSphericalPosition,
    MagnetThreeAxesRampRateController,
    SuperConductingMagnet,
    movement,
)
from dodal.devices.beamlines.i06_1.magnets.superconducting_magnet import (
    MODE_MOVEMENT_STRATEGY,
)
from tests.devices.beamlines.i06_1.magnets.utils import (
    EXPECTED_CARTESIAN_SPHERICAL_CONVERSION,
)


@pytest.fixture
def ramp_rate() -> MagnetThreeAxesRampRateController:
    with init_devices(mock=True):
        ramp_rate = MagnetThreeAxesRampRateController("TEST:")
    return ramp_rate


@pytest.fixture
def scmc(ramp_rate: MagnetThreeAxesRampRateController) -> SuperConductingMagnet:
    with init_devices(mock=True):
        scmc = SuperConductingMagnet("TEST:", ramp_rate)
    return scmc


async def test_scmc_read(scmc: SuperConductingMagnet) -> None:
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


async def test_scmc_configuration(scmc: SuperConductingMagnet) -> None:
    await assert_configuration(
        scmc, {"scmc-mode": partial_reading(MagnetModes.UNIAXIAL_X)}
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
    scmc: SuperConductingMagnet,
    axis: str,
    value: float,
    expected_x: float,
    expected_y: float,
    expected_z: float,
) -> None:
    await scmc.mode.set(getattr(MagnetModes, "UNIAXIAL_" + axis.capitalize()))
    await getattr(scmc.cart, axis).set(value)
    x, y, z = await asyncio.gather(
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x == expected_x
    assert y == expected_y
    assert z == expected_z


def test_cartesian_and_spherical_are_inverse() -> None:
    cartesian = MagnetPosition(x=10, y=20, z=30)
    result = cartesian.to_spherical().to_cartesian()
    assert result.x == pytest.approx(cartesian.x)
    assert result.y == pytest.approx(cartesian.y)
    assert result.z == pytest.approx(cartesian.z)


def test_spherical_and_cartesian_are_inverse() -> None:
    spherical = MagnetSphericalPosition(rho=10, theta=20, phi=30)
    result = spherical.to_cartesian().to_spherical()
    assert result.rho == pytest.approx(spherical.rho)
    assert result.theta == pytest.approx(spherical.theta)
    assert result.phi == pytest.approx(spherical.phi)


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
def test_cartesian_and_spherical_conversion_is_correct(
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    result = cartesian.to_spherical()
    assert result.rho == pytest.approx(spherical.rho)
    assert result.theta == pytest.approx(spherical.theta)
    assert result.phi == pytest.approx(spherical.phi)

    result = spherical.to_cartesian()
    assert result.x == pytest.approx(cartesian.x)
    assert result.y == pytest.approx(cartesian.y)
    assert result.z == pytest.approx(cartesian.z)


@pytest.mark.parametrize(
    "cartesian, spherical", EXPECTED_CARTESIAN_SPHERICAL_CONVERSION
)
async def test_scmc_set_using_spherical(
    scmc: SuperConductingMagnet,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scmc.mode.set(MagnetModes.SPHERICAL)
    await scmc.sph.set(spherical)
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
async def test_scmc_set_using_cartesian(
    scmc: SuperConductingMagnet,
    cartesian: MagnetPosition,
    spherical: MagnetSphericalPosition,
) -> None:
    await scmc.mode.set(MagnetModes.CUBIC)
    await scmc.cart.set(cartesian)
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
    "axis, value, expected_spherical",
    [
        ("rho", 2, MagnetSphericalPosition(rho=2, theta=20, phi=30)),
        ("theta", 40, MagnetSphericalPosition(rho=1, theta=40, phi=30)),
        ("phi", 60, MagnetSphericalPosition(rho=1, theta=20, phi=60)),
    ],
)
async def test_scmc_spherical_axis_set(
    scmc: SuperConductingMagnet,
    axis: str,
    value: float,
    expected_spherical: MagnetSphericalPosition,
) -> None:
    await scmc.mode.set(MagnetModes.SPHERICAL)
    # Start from a non-singular position.
    await scmc.sph.set(MagnetSphericalPosition(rho=1, theta=20, phi=30))
    await getattr(scmc.sph, axis).set(value)

    rho, theta, phi = await asyncio.gather(
        scmc.sph.rho.get_value(),
        scmc.sph.theta.get_value(),
        scmc.sph.phi.get_value(),
    )
    assert rho == pytest.approx(expected_spherical.rho)
    assert theta == pytest.approx(expected_spherical.theta)
    assert phi == pytest.approx(expected_spherical.phi)

    expected_cartesian = expected_spherical.to_cartesian()
    x, y, z = await asyncio.gather(
        scmc.cart.x.readback.get_value(),
        scmc.cart.y.readback.get_value(),
        scmc.cart.z.readback.get_value(),
    )
    assert x == pytest.approx(expected_cartesian.x)
    assert y == pytest.approx(expected_cartesian.y)
    assert z == pytest.approx(expected_cartesian.z)


async def test_scmc_raises_error_if_limit_status_is_violation(
    scmc: SuperConductingMagnet,
) -> None:
    await scmc.mode.set(MagnetModes.UNIAXIAL_X)
    set_mock_value(scmc.limit_status, MagnetLimitStatus.VIOLTATION)
    with pytest.raises(RuntimeError):
        await scmc.cart.x.set(1)


# @pytest.mark.parametrize(
#     "initial, target, expected_calls",
#     [
#         (
#             MagnetPosition(x=10, y=10, z=10),
#             MagnetPosition(x=20, y=5, z=2),
#             [
#                 call.z(2),
#                 call.ramp(),
#                 call.y(5),
#                 call.ramp(),
#                 call.x(20),
#                 call.y(5),
#                 call.z(2),
#                 call.ramp(),
#             ],
#         ),
#         (
#             MagnetPosition(x=10, y=10, z=10),
#             MagnetPosition(x=5, y=20, z=2),
#             [
#                 call.z(2),
#                 call.ramp(),
#                 call.x(5),
#                 call.ramp(),
#                 call.x(5),
#                 call.y(20),
#                 call.z(2),
#                 call.ramp(),
#             ],
#         ),
#         (
#             MagnetPosition(x=10, y=10, z=10),
#             MagnetPosition(x=5, y=2, z=20),
#             [
#                 call.x(5),
#                 call.ramp(),
#                 call.y(2),
#                 call.ramp(),
#                 call.x(5),
#                 call.y(2),
#                 call.z(20),
#                 call.ramp(),
#             ],
#         ),
#         (
#             MagnetPosition(x=10, y=10, z=10),
#             MagnetPosition(x=5, y=5, z=2),
#             [
#                 call.z(2),
#                 call.ramp(),
#                 call.x(5),
#                 call.ramp(),
#                 call.y(5),
#                 call.ramp(),
#             ],
#         ),
#     ],
# )
# async def test_scmc_set_decreases_before_increases(
#     scmc: SuperConductingMagnet,
#     initial: MagnetPosition,
#     target: MagnetPosition,
#     expected_calls,
# ) -> None:
#     await scmc.set(initial)

#     calls = []
#     scmc.x.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.x(v)))
#     scmc.y.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.y(v)))
#     scmc.z.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.z(v)))
#     scmc._ramp = AsyncMock(side_effect=lambda: calls.append(call.ramp()))

#     await scmc.set(target)
#     assert calls == expected_calls


async def test_scmc_set_within_boundary_raises_error_if_all_values_none(
    scmc: SuperConductingMagnet,
) -> None:
    with pytest.raises(MagnetPositionError):
        await scmc.set_within_boundary()


@pytest.mark.parametrize(
    "axis, mode",
    [
        ("x", MagnetModes.UNIAXIAL_X),
        ("y", MagnetModes.UNIAXIAL_Y),
        ("z", MagnetModes.UNIAXIAL_Z),
    ],
)
async def test_scmc_axis_with_ramp_rate_wired_correctly_with_prepare(
    scmc: SuperConductingMagnet,
    ramp_rate: MagnetThreeAxesRampRateController,
    axis: str,
    mode: MagnetModes,
) -> None:
    await scmc.mode.set(mode)
    magnet_axis: MagnetAxis = getattr(scmc.cart, axis)
    ramp_axis: MagnetAxisRampRateController = getattr(ramp_rate, axis)

    fly_info = FlyMagnetInfo(start_position=1, end_position=6, ramp_rate=4)
    await magnet_axis.prepare(fly_info)
    assert await magnet_axis.demand.get_value() == fly_info.start_position
    assert await ramp_axis.demand.get_value() == fly_info.ramp_rate


async def test_scmc_axis_kickoff_and_complete(scmc: SuperConductingMagnet) -> None:
    await scmc.mode.set(MagnetModes.UNIAXIAL_X)
    fly_info = FlyMagnetInfo(start_position=1, end_position=2, ramp_rate=4)
    assert scmc.cart.x._fly_info is None
    await scmc.cart.x.prepare(fly_info)
    assert scmc.cart.x._fly_info is fly_info
    assert scmc.cart.x._fly_status is None
    await scmc.cart.x.kickoff()
    assert scmc.cart.x._fly_info is None
    await scmc.cart.x.complete()
    assert await scmc.cart.x.readback.get_value() == fly_info.end_position


async def test_scmc_axis_kickoff_and_complete_raises_error_without_prepare(
    scmc: SuperConductingMagnet,
):
    await scmc.mode.set(MagnetModes.UNIAXIAL_X)
    # Do multiple times to make sure you cannot kickoff or complete without preparing
    # each time
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await scmc.cart.x.kickoff()

        with pytest.raises(RuntimeError):
            await scmc.cart.x.complete()

        fly_info = FlyMagnetInfo(start_position=1, end_position=2, ramp_rate=4)
        await scmc.cart.x.prepare(fly_info)
        await scmc.cart.x.kickoff()
        await scmc.cart.x.complete()


async def test_scmc_mock_device_behaviour(scmc: SuperConductingMagnet) -> None:
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
    await scmc.mode.set(MagnetModes.UNIAXIAL_X)

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


@pytest.mark.parametrize(
    "mode,expected",
    [
        (MagnetModes.SPHERICAL, movement.SphericalMovement),
        (MagnetModes.CUBIC, movement.CubicMovement),
        (MagnetModes.PLANAR_XZ, movement.PlanarXZMovement),
        (MagnetModes.QUADRANT_XY, movement.QuadrantXYMovement),
        (MagnetModes.UNIAXIAL_X, movement.UniaxialMovement),
        (MagnetModes.UNIAXIAL_Y, movement.UniaxialMovement),
        (MagnetModes.UNIAXIAL_Z, movement.UniaxialMovement),
    ],
)
async def test_magnet_mode_to_movement_strategy_configuration(
    mode: MagnetModes, expected: type[movement.MovementStrategy]
) -> None:
    assert isinstance(MODE_MOVEMENT_STRATEGY[mode], expected)


async def test_magnet_mode_to_uniaxial_movement_strategy_configuration():
    assert MODE_MOVEMENT_STRATEGY[MagnetModes.UNIAXIAL_X].axis == "x"  # type:ignore
    assert MODE_MOVEMENT_STRATEGY[MagnetModes.UNIAXIAL_Y].axis == "y"  # type:ignore
    assert MODE_MOVEMENT_STRATEGY[MagnetModes.UNIAXIAL_Z].axis == "z"  # type:ignore


async def test_scmc_executes_movement_stragey_and_ramp_at_each_step(
    scmc: SuperConductingMagnet,
) -> None:

    movement_strategy = MagicMock()

    mov_str_return_values = [
        movement.MagnetStep(z=2),
        movement.MagnetStep(x=1, y=2, z=3),
    ]
    expected_apply_step_calls = [
        call(movement.MagnetStep(z=2)),
        call(movement.MagnetStep(x=1, y=2, z=3)),
    ]
    movement_strategy.moves.return_value = mov_str_return_values

    MODE_MOVEMENT_STRATEGY[MagnetModes.UNIAXIAL_X] = movement_strategy

    scmc._ramp = AsyncMock()

    with patch(
        "dodal.devices.beamlines.i06_1.magnets.superconducting_magnet.SuperConductingMagnet._apply_step",
        wraps=scmc._apply_step,
    ) as mock_apply_step:
        await scmc.mode.set(MagnetModes.UNIAXIAL_X)
        await scmc.cart.x.set(4)

        assert mock_apply_step.call_args_list == expected_apply_step_calls
        assert scmc._ramp.call_count == len(mov_str_return_values)
