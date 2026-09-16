import pytest

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.attenuator_team import (
    BackstopLogicalTeam,
    WedgeOnlyTeam,
)
from dodal.devices.beamlines.i19.transmission.transmission_api import (
    AttenuatorTeam,
)

# tests on the happy path

def test_that_wedge_only_team_syntactically_upholds_attenuator_team_api() -> None:
    wedge_only_team: WedgeOnlyTeam = WedgeOnlyTeam()
    assert isinstance(wedge_only_team, AttenuatorTeam)

def test_that_backstop_team_syntactically_upholds_attenuator_team_api() -> None:
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert isinstance(bslt, AttenuatorTeam)


async def test_that_backstop_team_is_perennially_retracted() -> None:
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert await bslt.is_validly_positioned()


async def test_that_backstop_team_is_perennially_validly_positioned() -> None:
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert await bslt.is_validly_positioned()


@pytest.mark.parametrize(
    "parametric_energy_kev",
    (
        0.100,
        0.67345,
        1.3,
        3.456,
        7.812,
        11.094,
        13.640,
        24.908,
        45.023,
    ),
)
def test_that_backstop_team_accommodates_attenuation_demand_at_any_energy(
    parametric_energy_kev,
) -> None:
    _attenuation_demand = 1206.78  # Bn
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert bslt.can_accommodate(
        attenuation_demand_bn=_attenuation_demand, energy_kev=parametric_energy_kev
    )


@pytest.mark.parametrize(
    "parametric_attenuation_bn",
    (
        0,
        100,
        673.45,
        1300,
        2456.4,
        3812.1,
    ),
)
def test_that_backstop_team_accommodates_any_attenuation_demand(
    parametric_attenuation_bn,
) -> None:
    _energy_kev = 15.678  # arbitrary
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert bslt.can_accommodate(
        attenuation_demand_bn=parametric_attenuation_bn, energy_kev=_energy_kev
    )


def test_that_reported_backstop_motor_position_is_empty() -> None:
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert bslt.merge_in_retraction_motor_positions().is_empty()


@pytest.mark.parametrize(
    "motor_positions",
    [
        AttenuatorMotorPositions(
            discrete_indices={"w": 4}, continuous_positions={"x": -3.2, "y": 47.2}
        ),
        AttenuatorMotorPositions(
            discrete_indices={"w": 1}, continuous_positions={"y": -12.2}
        ),
        AttenuatorMotorPositions(
            discrete_indices={}, continuous_positions={"x": 83.2, "y": -12.2}
        ),
        AttenuatorMotorPositions(
            discrete_indices={}, continuous_positions={"y": -44.8}
        ),
        AttenuatorMotorPositions(),
    ],
)
def test_that_other_motor_positions_merged_into_backstop_motor_positions_are_unaltered(
    motor_positions: AttenuatorMotorPositions,
) -> None:
    bslt: BackstopLogicalTeam = BackstopLogicalTeam()
    assert (
        bslt.merge_in_retraction_motor_positions(other_motor_positions=motor_positions)
        == motor_positions
    )
