import pytest

from dodal.devices.beamlines.i06_1.magnets.coordinates import (
    MagnetPosition,
    MagnetRequest,
    MagnetSphericalPosition,
    MagnetSphericalRequest,
)
from dodal.devices.beamlines.i06_1.magnets.enums import MagnetMode
from dodal.devices.beamlines.i06_1.magnets.movement import (
    CubicMovement,
    MagnetPositionError,
    PlanarXZMovement,
    QuadrantXYMovement,
    SphericalMovement,
    UniaxialMovement,
)
from tests.devices.beamlines.i06_1.magnets.utils import (
    EXPECTED_CARTESIAN_SPHERICAL_CONVERSION,
)


def test_magnet_position_error_total_field_mag_outside_limit():
    position = MagnetPosition(x=1.0, y=2.0, z=3.0)
    error = MagnetPositionError.total_field_mag_outside_limit(
        MagnetMode.SPHERICAL, 1.75, position
    )
    assert isinstance(error, MagnetPositionError)
    assert str(error) == (
        f"Target field magnitude of {position.field_magnitude} T exceeds "
        f"limit of 1.75 for mode {MagnetMode.SPHERICAL}. Requested position: {position}."
    )


def test_magnet_position_error_axis_outside_limit():
    error = MagnetPositionError.axis_outside_limit(MagnetMode.CUBIC, 1.5, 2.0, "x")
    assert isinstance(error, MagnetPositionError)
    assert str(error) == (
        f"Axis x with value 2.0 exceeds limit 1.5 T for mode {MagnetMode.CUBIC}."
    )


def test_magnet_position_error_axis_must_be_zero():
    error = MagnetPositionError.axis_must_be_zero(MagnetMode.PLANAR_XZ, "y", 1.0)
    assert isinstance(error, MagnetPositionError)
    assert str(error) == (
        f"Axis y must remain zero for mode {MagnetMode.PLANAR_XZ}. "
        "Requested value was 1.0."
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
        MagnetRequest()
    with pytest.raises(ValueError):
        MagnetSphericalRequest()


@pytest.mark.parametrize(
    "current, target, expected",
    [
        # All decreases done as one move.
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetRequest(x=1, y=1, z=1),
            [MagnetRequest(x=1, y=1, z=1)],
        ),
        # Check decreases done as one move and done before the increase
        (
            MagnetPosition(x=3, y=3, z=3),
            MagnetRequest(x=4, y=2, z=1),
            [
                MagnetRequest(y=2, z=1),
                MagnetRequest(x=4),
            ],
        ),
        # Check if all an increase, all done together
        (
            MagnetPosition(x=1, y=1, z=1),
            MagnetRequest(x=2, y=2, z=2),
            [
                MagnetRequest(x=2, y=2, z=2),
            ],
        ),
        # Check requesting same position will do no movement
        (
            MagnetPosition(x=1, y=2, z=3),
            MagnetRequest(x=1, y=2, z=3),
            [],
        ),
    ],
)
def test_spherical_movement(
    current: MagnetPosition,
    target: MagnetRequest,
    expected: list[MagnetRequest],
) -> None:
    assert SphericalMovement().move_steps(current, target) == expected


def test_spherical_movement_within_limit():
    current = MagnetPosition(x=0.0, y=0.0, z=0.0)
    target = MagnetRequest(x=1.0, y=0.0, z=0.0)
    SphericalMovement().check_within_limit(current, target)


def test_spherical_movement_outside_limit_raises_error():
    current = MagnetPosition(x=0.0, y=0.0, z=0.0)
    target = MagnetRequest(x=2.0, y=0.0, z=0.0)
    with pytest.raises(MagnetPositionError):
        SphericalMovement().check_within_limit(current, target)


def test_spherical_movement_at_limit_is_allowed():
    current = MagnetPosition(x=0.0, y=0.0, z=0.0)
    target = MagnetRequest(x=1.75, y=0.0, z=0.0)
    SphericalMovement().check_within_limit(current, target)


@pytest.mark.parametrize(
    "target",
    [
        MagnetRequest(x=1.6, y=0, z=0),
        MagnetRequest(x=0, y=-1.6, z=0),
        MagnetRequest(x=0, y=0, z=2),
    ],
)
def test_cubic_rejects_outside_limits(target: MagnetRequest) -> None:
    with pytest.raises(MagnetPositionError):
        CubicMovement().check_within_limits(MagnetPosition(x=0, y=0, z=0), target)


def test_cubic_returns_single_step() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetRequest(x=1, y=1.2, z=-0.5)
    assert CubicMovement().move_steps(current, target) == [
        MagnetRequest(x=1, y=1.2, z=-0.5)
    ]


def test_planar_xz_returns_single_step() -> None:
    target = MagnetRequest(x=1.2, y=0, z=-0.4)
    assert PlanarXZMovement().move_steps(MagnetPosition(x=0, y=0, z=0), target) == [
        MagnetRequest(x=1.2, z=-0.4),
    ]


def test_planar_xz_rejects_nonzero_y() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetRequest(x=1, y=1, z=0)
        )


def test_planar_xz_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        PlanarXZMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetRequest(x=2, y=0, z=2)
        )


@pytest.mark.parametrize(
    "mode, limit, target",
    [
        (MagnetMode.UNIAXIAL_X, 2, MagnetRequest(x=1, y=0, z=0)),
        (MagnetMode.UNIAXIAL_Y, 2, MagnetRequest(x=0, y=-1, z=0)),
        (MagnetMode.UNIAXIAL_Z, 5, MagnetRequest(x=0, y=0, z=3)),
    ],
)
def test_uniaxial_returns_single_step(
    mode: MagnetMode, limit: float, target: MagnetRequest
) -> None:
    assert UniaxialMovement(mode, limit).move_steps(
        MagnetPosition(x=0, y=0, z=0), target
    ) == [MagnetRequest(**{mode.axis_alias: getattr(target, mode.axis_alias)})]


@pytest.mark.parametrize(
    "mode, target",
    [
        (MagnetMode.UNIAXIAL_X, MagnetRequest(x=1, y=1, z=0)),
        (MagnetMode.UNIAXIAL_X, MagnetRequest(x=1, y=0, z=1)),
        (MagnetMode.UNIAXIAL_Y, MagnetRequest(x=1, y=1, z=0)),
        (MagnetMode.UNIAXIAL_Y, MagnetRequest(x=0, y=1, z=1)),
        (MagnetMode.UNIAXIAL_Z, MagnetRequest(x=1, y=0, z=1)),
        (MagnetMode.UNIAXIAL_Z, MagnetRequest(x=0, y=1, z=1)),
    ],
)
def test_uniaxial_rejects_other_axes(mode: MagnetMode, target: MagnetRequest) -> None:
    with pytest.raises(MagnetPositionError):
        UniaxialMovement(mode, limit=5).check_within_limits(
            MagnetPosition(x=0, y=0, z=0), target
        )


def test_uniaxial_raise_error_when_above_limit() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetRequest(x=10, y=0, z=0)
    with pytest.raises(MagnetPositionError):
        UniaxialMovement(MagnetMode.UNIAXIAL_X, limit=5).check_within_limits(
            current, target
        )


def test_quadrant_xy_sequence() -> None:
    current = MagnetPosition(x=1, y=0.5, z=0)
    target = MagnetRequest(x=1.5, y=1, z=0)
    assert QuadrantXYMovement().move_steps(current, target) == [
        MagnetRequest(x=0),
        MagnetRequest(y=1),
        MagnetRequest(x=1.5),
    ]


def test_quadrant_xy_skips_initial_x_zero() -> None:
    current = MagnetPosition(x=0, y=0, z=0)
    target = MagnetRequest(x=1, y=1, z=0)
    assert QuadrantXYMovement().move_steps(current, target) == [
        MagnetRequest(y=1),
        MagnetRequest(x=1),
    ]


def test_quadrant_xy_skips_y_move() -> None:
    target = MagnetPosition(x=1, y=1.5, z=0)
    current = MagnetRequest(x=0.5, y=1.5, z=0)
    assert QuadrantXYMovement().move_steps(target, current) == [
        MagnetRequest(x=0),
        MagnetRequest(x=0.5),
    ]


def test_quadrant_xy_rejects_nonzero_z() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetRequest(x=1, y=1, z=1)
        )


def test_quadrant_xy_rejects_outside_radius() -> None:
    with pytest.raises(MagnetPositionError):
        QuadrantXYMovement().check_within_limits(
            MagnetPosition(x=0, y=0, z=0), MagnetRequest(x=2, y=2, z=0)
        )
