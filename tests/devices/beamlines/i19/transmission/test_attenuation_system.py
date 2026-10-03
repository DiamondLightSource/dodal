
from unittest.mock import AsyncMock

import pytest

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.attenuation_system import (
    AttenuationSystem,
    Team,
)

# tests on the happy path

async def test_that_requests_to_read_motor_positions_are_passed_to_subsystems() -> None:
    mock_subsystems: list[AsyncMock] = [AsyncMock(spec=Team)]
    attenuation_system:AttenuationSystem = AttenuationSystem(*mock_subsystems)
    for subsystem in mock_subsystems:
            subsystem.current_motor_positions.assert_not_awaited()
    await attenuation_system.get_current_motor_positions()
    for subsystem in mock_subsystems:
        subsystem.current_motor_positions.assert_awaited_once()


@pytest.mark.parametrize(
    "subsystem_positions, expected_result",
    [
        (
            [
                ({},{},)  # motor positions - only one subsystem
            ],
            {}  # expected result
        ),
        (
            [
                ({"y": 49.4},{"w":2}),
                ({"x": -1.04},{})
            ],
            {"x": -1.04, "y": 49.4, "w": 2}
        ),
        (
            [
                ({"y": 7.8},{}),
                ({"x": 28.34},{})
            ],
            {"x": 28.34, "y": 7.8}
        ),
        (
            [
                ({"y": 27.08},{"w":3}),
                ({},{})
            ],
            {"w": 3, "y": 27.08}
        )
    ]
)
async def test_that_collated_motor_positions_reading_is_faithful_to_subsystem_reports(
    subsystem_positions: list[tuple[dict[str,float],dict[str,int]]], expected_result: dict[str,float|int]
) -> None:

    # start set up
    motor_positions: list[AttenuatorMotorPositions] = [
         AttenuatorMotorPositions(continuous_positions=wedge_positions, discrete_indices=wheel_indices)
         for wedge_positions, wheel_indices in subsystem_positions
    ]

    # auxiliary method to help set up
    def mocked_out_subsystem(example_motor_pos: AttenuatorMotorPositions):
        mocked_subsystem = AsyncMock(spec=Team)
        mocked_subsystem.current_motor_positions.return_value = example_motor_pos
        return mocked_subsystem

    # complete set up
    mock_subsystems: list[AsyncMock] = [
        mocked_out_subsystem(p) for p in motor_positions
    ]
    attenuation_system: AttenuationSystem = AttenuationSystem(*mock_subsystems)

    # stress the method on trial
    report = await attenuation_system.get_current_motor_positions()

    # assert happy path expectations
    assert report.validated_and_complete == expected_result


@pytest.mark.parametrize(
    "retracted_states, active_subsystem_in_list",
    [
        ([True, False], 1),
        ([False, True], 0),
        ([True, True], None),
        ([True], None),
        ([False], 0),
    ]
)
# Note: On the happy path - either zero or one subsystem is active ( active = not retracted )
def test_that_internal_search_for_active_subsystems_correctly_excludes_retracted_subsystems(
    retracted_states:list[bool],
    active_subsystem_in_list: int | None) -> None:

    # auxiliary method to help set up
    def mocked_out_subsystem(retracted_state: bool):
        mocked_subsystem = AsyncMock(spec=Team)
        mocked_subsystem.is_retracted_at.return_value = retracted_state
        return mocked_subsystem

    # set up test resources
    mock_subsystems: list [AsyncMock] = [
        mocked_out_subsystem(r) for r in retracted_states
    ]
    attenuation_system: AttenuationSystem = AttenuationSystem(*mock_subsystems)
    amp_example: AttenuatorMotorPositions = (
        AttenuatorMotorPositions(continuous_positions={"x": -12.2, "y": 31.779},
                                 discrete_indices={"u":4})
    )

    # stress the method on trial
    report: list[Team] = attenuation_system._find_unretracted_teams_if_motors_were_at(motor_positions=amp_example)

    # assert sentinel mock falls through filtering search
    if active_subsystem_in_list is not None:  # have to remember zero is considered false in C / Python
        assert len(report) == 1  # assert survivor was unique
        assert report[0] is mock_subsystems[active_subsystem_in_list]  # assert sentinel mock came through finding
    else:
        assert len(report) < 1  # or else assert anticipated blank result from search


@pytest.mark.parametrize(
    "bn_per_subsystem, retracted_states,expected_total_bn",
    [
        (345.82, [True], CANONICAL_NON_ABSORPTION),
        (561.4, [True, False], 561.4),
        (2200, [False, True], 2200),
        (1150.7, [True, True], CANONICAL_NON_ABSORPTION),
        (978.31663, [False], 978.31663),
    ]
)
# Note: On the happy path - either zero or one subsystem is active ( active = not retracted )
def test_that_attenuation_report_is_based_on_subsystem_reports_of_attenuation_and_retraction_state(
    bn_per_subsystem: float,
    retracted_states:list[bool],
    expected_total_bn,
) -> None:

    # auxiliary method to help set up
    def mocked_out_subsystem(*, retracted_state: bool, attenuation_bn: float):
        mocked_subsystem = AsyncMock(spec=Team)
        mocked_subsystem.is_retracted_at.return_value = retracted_state
        mocked_subsystem.predict_attenuation_at.return_value = (
            attenuation_bn
        )
        return mocked_subsystem

    # set up test resources
    mock_subsystems: list [AsyncMock] = [
        mocked_out_subsystem(
            retracted_state=r,
            attenuation_bn=bn_per_subsystem
        )
        for r in retracted_states
    ]
    attenuation_system: AttenuationSystem = AttenuationSystem(*mock_subsystems)

    # stress the method on trial
    reported_bn: float = (
        attenuation_system.predict_attenuation_bn_at(
            energy_kev=21398.47,  # arbitrary and irrelevant here
            motor_positions=AttenuatorMotorPositions()
        )
    )
    assert reported_bn == pytest.approx(expected=expected_total_bn)
