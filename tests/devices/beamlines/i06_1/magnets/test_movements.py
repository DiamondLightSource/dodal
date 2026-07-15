import pytest

from dodal.devices.beamlines.i06_1.magnets.movement import (
    CubicMovement,
    MagnetPosition,
    MagnetPositionError,
    MagnetSphericalPosition,
    MagnetStep,
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


def test_spherical_movement_decreases_z_then_x_then_y() -> None:
    move_stragegy = SphericalMovement()
    steps = move_stragegy.moves(
        current=MagnetPosition(x=10, y=10, z=10),
        target=MagnetPosition(x=5, y=5, z=2),
    )
    assert steps == [MagnetStep(z=2), MagnetStep(x=5), MagnetStep(y=5)]


def test_spherical_movement_adds_final_combined_increase() -> None:
    move_stragegy = SphericalMovement()
    steps = move_stragegy.moves(
        current=MagnetPosition(x=10, y=10, z=10),
        target=MagnetPosition(x=20, y=5, z=2),
    )
    assert steps == [MagnetStep(z=2), MagnetStep(y=5), MagnetStep(x=20, y=5, z=2)]


@pytest.mark.parametrize(
    "current, target, expected",
    [
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetPosition(x=1, y=1, z=1),
            [
                MagnetStep(z=1),
                MagnetStep(x=1),
                MagnetStep(y=1),
            ],
        ),
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetPosition(x=4, y=2, z=1),
            [
                MagnetStep(z=1),
                MagnetStep(y=2),
                MagnetStep(x=4, y=2, z=1),
            ],
        ),
        (
            MagnetPosition(x=1, y=1, z=1),
            MagnetPosition(x=2, y=2, z=2),
            [
                MagnetStep(x=2, y=2, z=2),
            ],
        ),
        (
            MagnetPosition(x=1, y=2, z=3),
            MagnetPosition(x=1, y=2, z=3),
            [],
        ),
    ],
)
def test_spherical_movement(
    current: MagnetPosition, target: MagnetPosition, expected: list[MagnetStep]
) -> None:
    assert SphericalMovement().moves(current, target) == expected


@pytest.mark.parametrize(
    "target",
    [
        MagnetPosition(x=1.6, y=0, z=0),
        MagnetPosition(x=0, y=-1.6, z=0),
        MagnetPosition(x=0, y=0, z=2),
    ],
)
def test_cubic_rejects_outside_limits(target: MagnetPosition) -> None:
    with pytest.raises(MagnetPositionError):
        CubicMovement().moves(MagnetPosition(x=0, y=0, z=0), target)


def test_cubic_returns_single_step() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPosition(x=1, y=1.2, z=-0.5)

    assert CubicMovement().moves(current, target) == [MagnetStep(x=1, y=1.2, z=-0.5)]


def test_planar_xz_returns_single_step() -> None:
    target = MagnetPosition(x=1.2, y=0, z=-0.4)

    assert PlanarXZMovement().moves(MagnetPosition(x=0, y=0, z=0), target) == [
        MagnetStep(x=1.2, z=-0.4),
    ]


def test_planar_xz_rejects_nonzero_y() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().moves(
            MagnetPosition(x=0, y=0, z=0), MagnetPosition(x=1, y=1, z=0)
        )


def test_planar_xz_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().moves(
            MagnetPosition(x=0, y=0, z=0), MagnetPosition(x=2, y=0, z=2)
        )


@pytest.mark.parametrize(
    "axis, limit, target",
    [
        ("x", 2, MagnetPosition(x=1, y=0, z=0)),
        ("y", 2, MagnetPosition(x=0, y=-1, z=0)),
        ("z", 5, MagnetPosition(x=0, y=0, z=3)),
    ],
)
def test_uniaxial_returns_single_step(
    axis: str, limit: float, target: MagnetPosition
) -> None:
    assert UniaxialMovement(axis, limit).moves(
        MagnetPosition(x=0, y=0, z=0), target
    ) == [MagnetStep(**{axis: getattr(target, axis)})]


@pytest.mark.parametrize(
    "axis,target",
    [
        ("x", MagnetPosition(x=1, y=1, z=0)),
        ("x", MagnetPosition(x=1, y=0, z=1)),
        ("y", MagnetPosition(x=1, y=1, z=0)),
        ("y", MagnetPosition(x=0, y=1, z=1)),
        ("z", MagnetPosition(x=1, y=0, z=1)),
        ("z", MagnetPosition(x=0, y=1, z=1)),
    ],
)
def test_uniaxial_rejects_other_axes(axis: str, target: MagnetPosition) -> None:
    with pytest.raises(MagnetPositionError):
        UniaxialMovement(axis, limit=5).moves(MagnetPosition(x=0, y=0, z=0), target)


def test_uniaxial_raise_error_when_above_limit() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPosition(x=10, y=0, z=0)
    with pytest.raises(MagnetPositionError):
        UniaxialMovement("x", limit=5).moves(current, target)


def test_quadrant_xy_sequence() -> None:
    current = MagnetPosition(x=1, y=0.5, z=0)
    target = MagnetPosition(x=1.5, y=1, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.moves(current, target) == [
        MagnetStep(x=0),
        MagnetStep(y=1),
        MagnetStep(x=1.5),
    ]


def test_quadrant_xy_skips_initial_x_zero() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetPosition(x=1, y=1, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.moves(current, target) == [MagnetStep(y=1), MagnetStep(x=1)]


def test_quadrant_xy_skips_y_move() -> None:
    target = MagnetPosition(x=1, y=1.5, z=0)
    current = MagnetPosition(x=0.5, y=1.5, z=0)
    strategy = QuadrantXYMovement()
    assert strategy.moves(target, current) == [MagnetStep(x=0), MagnetStep(x=0.5)]


def test_quadrant_xy_rejects_nonzero_z() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().moves(
            MagnetPosition(x=0, y=0, z=0), MagnetPosition(x=1, y=1, z=1)
        )


def test_quadrant_xy_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().moves(
            MagnetPosition(x=0, y=0, z=0), MagnetPosition(x=2, y=2, z=0)
        )
