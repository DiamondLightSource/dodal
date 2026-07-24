import pytest

from dodal.devices.beamlines.i06_1.magnets.enums import MagnetModes
from dodal.devices.beamlines.i06_1.magnets.movement import (
    CubicMovement,
    MagnetPosition,
    MagnetPositionError,
    MagnetPositionRequest,
    MagnetSphericalPosition,
    PlanarXZMovement,
    QuadrantXYMovement,
    SphericalMovement,
    UniaxialMovement,
)
from tests.devices.beamlines.i06_1.magnets.utils import (
    EXPECTED_CARTESIAN_SPHERICAL_CONVERSION,
)


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
    cartesian: MagnetPosition, spherical: MagnetSphericalPosition
) -> None:
    result = cartesian.to_spherical()
    assert result.rho == pytest.approx(spherical.rho)
    assert result.theta == pytest.approx(spherical.theta)
    assert result.phi == pytest.approx(spherical.phi)

    result = spherical.to_cartesian()
    assert result.x == pytest.approx(cartesian.x)
    assert result.y == pytest.approx(cartesian.y)
    assert result.z == pytest.approx(cartesian.z)


def test_all_none_values_for_magnet_position_request_raises_error():
    with pytest.raises(ValueError):
        MagnetPositionRequest()


# Doesn't matter order we decrease?
# def test_spherical_movement_decreases_z_then_x_then_y() -> None:
#     move_stragegy = SphericalMovement()
#     steps = move_stragegy.moves(
#         current=MagnetPosition(x=10, y=10, z=10),
#         target=MagnetPositionRequest(x=5, y=5, z=2),
#     )
#     assert steps == [
#         MagnetPositionRequest(z=2),
#         MagnetPositionRequest(x=5),
#         MagnetPositionRequest(y=5),
#     ]


@pytest.mark.parametrize(
    "current, target, expected",
    [
        # All decreases done as one move.
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetPositionRequest(x=1, y=1, z=1),
            [MagnetPositionRequest(x=1, y=1, z=1)],
        ),
        # Check decreases done as one move and done before the increase
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetPositionRequest(x=4, y=2, z=1),
            [
                MagnetPositionRequest(y=2, z=1),
                MagnetPositionRequest(x=4),
            ],
        ),
        # Check if all an increase, all done together
        (
            MagnetPosition(x=1, y=1, z=1),
            MagnetPositionRequest(x=2, y=2, z=2),
            [
                MagnetPositionRequest(x=2, y=2, z=2),
            ],
        ),
        # Check requesting same position will do no movement
        (
            MagnetPosition(x=1, y=2, z=3),
            MagnetPositionRequest(x=1, y=2, z=3),
            [],
        ),
    ],
)
def test_spherical_movement(
    current: MagnetPosition,
    target: MagnetPositionRequest,
    expected: list[MagnetPositionRequest],
) -> None:
    assert SphericalMovement().move_steps(current, target) == expected


@pytest.mark.parametrize(
    "target",
    [
        MagnetPositionRequest(x=1.6, y=0, z=0),
        MagnetPositionRequest(x=0, y=-1.6, z=0),
        MagnetPositionRequest(x=0, y=0, z=2),
    ],
)
def test_cubic_rejects_outside_limits(target: MagnetPositionRequest) -> None:
    with pytest.raises(MagnetPositionError):
        CubicMovement().check_within_limits(MagnetPosition(x=0, y=0, z=0), target)


def test_cubic_returns_single_step() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPositionRequest(x=1, y=1.2, z=-0.5)

    assert CubicMovement().move_steps(current, target) == [
        MagnetPositionRequest(x=1, y=1.2, z=-0.5)
    ]


def test_planar_xz_returns_single_step() -> None:
    target = MagnetPositionRequest(x=1.2, y=0, z=-0.4)

    assert PlanarXZMovement().move_steps(MagnetPosition(x=0, y=0, z=0), target) == [
        MagnetPositionRequest(x=1.2, z=-0.4),
    ]


def test_planar_xz_rejects_nonzero_y() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetPositionRequest(x=1, y=1, z=0)
        )


def test_planar_xz_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetPositionRequest(x=2, y=0, z=2)
        )


@pytest.mark.parametrize(
    "mode, limit, target",
    [
        (MagnetModes.UNIAXIAL_X, 2, MagnetPositionRequest(x=1, y=0, z=0)),
        (MagnetModes.UNIAXIAL_Y, 2, MagnetPositionRequest(x=0, y=-1, z=0)),
        (MagnetModes.UNIAXIAL_Z, 5, MagnetPositionRequest(x=0, y=0, z=3)),
    ],
)
def test_uniaxial_returns_single_step(
    mode: MagnetModes, limit: float, target: MagnetPositionRequest
) -> None:
    assert UniaxialMovement(mode, limit).move_steps(
        MagnetPosition(x=0, y=0, z=0), target
    ) == [MagnetPositionRequest(**{mode.axis_alias: getattr(target, mode.axis_alias)})]


@pytest.mark.parametrize(
    "mode, target",
    [
        (MagnetModes.UNIAXIAL_X, MagnetPositionRequest(x=1, y=1, z=0)),
        (MagnetModes.UNIAXIAL_X, MagnetPositionRequest(x=1, y=0, z=1)),
        (MagnetModes.UNIAXIAL_Y, MagnetPositionRequest(x=1, y=1, z=0)),
        (MagnetModes.UNIAXIAL_Y, MagnetPositionRequest(x=0, y=1, z=1)),
        (MagnetModes.UNIAXIAL_Z, MagnetPositionRequest(x=1, y=0, z=1)),
        (MagnetModes.UNIAXIAL_Z, MagnetPositionRequest(x=0, y=1, z=1)),
    ],
)
def test_uniaxial_rejects_other_axes(
    mode: MagnetModes, target: MagnetPositionRequest
) -> None:
    with pytest.raises(MagnetPositionError):
        UniaxialMovement(mode, limit=5).check_within_limits(
            MagnetPosition(x=0, y=0, z=0), target
        )


def test_uniaxial_raise_error_when_above_limit() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPositionRequest(x=10, y=0, z=0)
    with pytest.raises(MagnetPositionError):
        UniaxialMovement(MagnetModes.UNIAXIAL_X, limit=5).check_within_limits(
            current, target
        )


def test_quadrant_xy_sequence() -> None:
    current = MagnetPosition(x=1, y=0.5, z=0)
    target = MagnetPositionRequest(x=1.5, y=1, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.move_steps(current, target) == [
        MagnetPositionRequest(x=0),
        MagnetPositionRequest(y=1),
        MagnetPositionRequest(x=1.5),
    ]


def test_quadrant_xy_skips_initial_x_zero() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPositionRequest(x=1, y=1, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.move_steps(current, target) == [
        MagnetPositionRequest(y=1),
        MagnetPositionRequest(x=1),
    ]


def test_quadrant_xy_skips_y_move() -> None:
    target = MagnetPosition(x=1, y=1.5, z=0)
    current = MagnetPositionRequest(x=0.5, y=1.5, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.move_steps(target, current) == [
        MagnetPositionRequest(x=0),
        MagnetPositionRequest(x=0.5),
    ]


def test_quadrant_xy_rejects_nonzero_z() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetPositionRequest(x=1, y=1, z=1)
        )


def test_quadrant_xy_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetPositionRequest(x=2, y=2, z=0)
        )
