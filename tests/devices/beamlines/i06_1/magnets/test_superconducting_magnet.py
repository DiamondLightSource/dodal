import asyncio
from unittest.mock import AsyncMock, call

import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnets import (
    MagnetLimitStatus,
    MagnetPosition,
    MagnetSphericalPosition,
    MagnetThreeAxesRampRateController,
    SuperConductingMagnet,
)

EXPECTED_CARTESIAN_SPHERICAL_CONVERSION = [
    (MagnetPosition(x=0, y=0, z=1), MagnetSphericalPosition(rho=1, theta=0, phi=90)),
    (MagnetPosition(x=-1, y=0, z=0), MagnetSphericalPosition(rho=1, theta=90, phi=90)),
    (MagnetPosition(x=0, y=1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=0)),
    (MagnetPosition(x=0, y=-1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=180)),
]


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
            "scmc-x": partial_reading(0),
            "scmc-y": partial_reading(0),
            "scmc-z": partial_reading(0),
            "scmc-theta": partial_reading(0),
            "scmc-rho": partial_reading(0),
            "scmc-phi": partial_reading(0),
        },
    )


@pytest.mark.parametrize(
    "axis, value, expected_x, expected_y, expected_z",
    [
        ("x", 10, 10, 0, 0),
        ("y", 20, 0, 20, 0),
        ("z", 30, 0, 0, 30),
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
    await getattr(scmc, axis).set(value)
    x, y, z = await asyncio.gather(
        scmc.x.readback.get_value(),
        scmc.y.readback.get_value(),
        scmc.z.readback.get_value(),
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
    await scmc.set(spherical)
    rho, theta, phi = await asyncio.gather(
        scmc.rho.get_value(),
        scmc.theta.get_value(),
        scmc.phi.get_value(),
    )
    assert rho == pytest.approx(spherical.rho)
    assert theta == pytest.approx(spherical.theta)
    assert phi == pytest.approx(spherical.phi)

    x, y, z = await asyncio.gather(
        scmc.x.readback.get_value(),
        scmc.y.readback.get_value(),
        scmc.z.readback.get_value(),
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
    await scmc.set(cartesian)
    x, y, z = await asyncio.gather(
        scmc.x.readback.get_value(),
        scmc.y.readback.get_value(),
        scmc.z.readback.get_value(),
    )
    assert x == pytest.approx(cartesian.x)
    assert y == pytest.approx(cartesian.y)
    assert z == pytest.approx(cartesian.z)

    rho, theta, phi = await asyncio.gather(
        scmc.rho.get_value(),
        scmc.theta.get_value(),
        scmc.phi.get_value(),
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
    # Start from a non-singular position.
    await scmc.set(MagnetSphericalPosition(rho=1, theta=20, phi=30))
    await getattr(scmc, axis).set(value)

    rho, theta, phi = await asyncio.gather(
        scmc.rho.get_value(),
        scmc.theta.get_value(),
        scmc.phi.get_value(),
    )
    assert rho == pytest.approx(expected_spherical.rho)
    assert theta == pytest.approx(expected_spherical.theta)
    assert phi == pytest.approx(expected_spherical.phi)

    expected_cartesian = expected_spherical.to_cartesian()
    x, y, z = await asyncio.gather(
        scmc.x.readback.get_value(),
        scmc.y.readback.get_value(),
        scmc.z.readback.get_value(),
    )
    assert x == pytest.approx(expected_cartesian.x)
    assert y == pytest.approx(expected_cartesian.y)
    assert z == pytest.approx(expected_cartesian.z)


async def test_scmc_raises_error_if_limit_status_is_violation(
    scmc: SuperConductingMagnet,
) -> None:
    set_mock_value(scmc.limit_status, MagnetLimitStatus.VIOLTATION)
    with pytest.raises(RuntimeError):
        await scmc.x.set(10)


@pytest.mark.parametrize(
    "initial, target, expected_calls",
    [
        (
            MagnetPosition(x=10, y=10, z=10),
            MagnetPosition(x=20, y=5, z=2),
            [
                call.z(2),
                call.ramp(),
                call.y(5),
                call.ramp(),
                call.x(20),
                call.y(5),
                call.z(2),
                call.ramp(),
            ],
        ),
        (
            MagnetPosition(x=10, y=10, z=10),
            MagnetPosition(x=5, y=20, z=2),
            [
                call.z(2),
                call.ramp(),
                call.x(5),
                call.ramp(),
                call.x(5),
                call.y(20),
                call.z(2),
                call.ramp(),
            ],
        ),
        (
            MagnetPosition(x=10, y=10, z=10),
            MagnetPosition(x=5, y=2, z=20),
            [
                call.x(5),
                call.ramp(),
                call.y(2),
                call.ramp(),
                call.x(5),
                call.y(2),
                call.z(20),
                call.ramp(),
            ],
        ),
        (
            MagnetPosition(x=10, y=10, z=10),
            MagnetPosition(x=5, y=5, z=2),
            [
                call.z(2),
                call.ramp(),
                call.x(5),
                call.ramp(),
                call.y(5),
                call.ramp(),
            ],
        ),
    ],
)
async def test_scmc_set_decreases_before_increases(
    scmc: SuperConductingMagnet,
    initial: MagnetPosition,
    target: MagnetPosition,
    expected_calls,
) -> None:
    await scmc.set(initial)

    calls = []
    scmc.x.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.x(v)))
    scmc.y.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.y(v)))
    scmc.z.demand.set = AsyncMock(side_effect=lambda v: calls.append(call.z(v)))
    scmc._ramp = AsyncMock(side_effect=lambda: calls.append(call.ramp()))

    await scmc.set(target)
    assert calls == expected_calls


async def test_scmc_set_within_boundary_raises_error_if_all_values_none(
    scmc: SuperConductingMagnet,
) -> None:
    with pytest.raises(RuntimeError):
        await scmc.set_within_boundary()
