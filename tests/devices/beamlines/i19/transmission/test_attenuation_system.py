from unittest.mock import AsyncMock

import pytest

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.attenuation_system import (
    AttenuationSystem,
    AttenuatorTeam,
)

# auxiliary methods


def _given_a_set_of_subsystems_whose_motors_are_at(
    *,
    subsystem_positions: list[tuple[dict[str, float], dict[str, int]]],
) -> list[AsyncMock]:
    # start set up
    motor_positions: list[AttenuatorMotorPositions] = [
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions, discrete_indices=wheel_indices
        )
        for wedge_positions, wheel_indices in subsystem_positions
    ]

    # factory for churning out mocked instances
    def _mocked_out_subsystem(example_motor_pos: AttenuatorMotorPositions) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.current_motor_positions.return_value = example_motor_pos
        return mocked_subsystem

    # complete set up
    return [_mocked_out_subsystem(p) for p in motor_positions]


def _given_a_set_of_subsystems_retracted_per_these_states(
    *, retraction_states: list[bool]
) -> list[AsyncMock]:

    # factory for churning out mocked instances
    def _mocked_out_subsystem(retraction_state: bool) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.is_retracted_at.return_value = retraction_state
        return mocked_subsystem

    # set up test resources
    return [_mocked_out_subsystem(r) for r in retraction_states]


# tests on the happy path


async def test_that_requests_to_read_motor_positions_are_passed_to_subsystems() -> None:
    # set up test conditions
    mocked_subsystems: list[AsyncMock] = [AsyncMock(spec=AttenuatorTeam)]
    attenuation_system: AttenuationSystem = AttenuationSystem(*mocked_subsystems)
    # verify no calls made yet of methods which will be triggered
    for subsystem in mocked_subsystems:
        subsystem.current_motor_positions.assert_not_awaited()
    # exercise the method under trial
    await attenuation_system.get_current_motor_positions()
    # prove that the delegates were invoked as required
    for subsystem in mocked_subsystems:
        subsystem.current_motor_positions.assert_awaited_once()


@pytest.mark.parametrize(
    "subsystem_positions, expected_result",
    [
        (
            [
                (
                    {},
                    {},
                )  # motor positions - only one subsystem
            ],
            {},  # expected result
        ),
        (
            [({"y": 49.4}, {"w": 2}), ({"x": -1.04}, {})],
            {"x": -1.04, "y": 49.4, "w": 2},
        ),
        ([({"y": 7.8}, {}), ({"x": 28.34}, {})], {"x": 28.34, "y": 7.8}),
        ([({"y": 27.08}, {"w": 3}), ({}, {})], {"w": 3, "y": 27.08}),
    ],
)
async def test_that_collated_motor_positions_reading_is_faithful_to_subsystem_reports(
    subsystem_positions: list[tuple[dict[str, float], dict[str, int]]],
    expected_result: dict[str, float | int],
) -> None:
    # set up test conditions
    mock_subsystems = _given_a_set_of_subsystems_whose_motors_are_at(
        subsystem_positions=subsystem_positions
    )
    attenuation_system: AttenuationSystem = AttenuationSystem(*mock_subsystems)

    # stress the method on trial
    report = await attenuation_system.get_current_motor_positions()

    # assert happy path expectations
    assert report.validated_and_complete == expected_result


@pytest.mark.parametrize(
    "retraction_states, active_subsystem_in_list",
    [
        ([True, False], 1),
        ([False, True], 0),
        ([True, True], None),
        ([True], None),
        ([False], 0),
    ],
)
# Note: On the happy path - either zero or one subsystem is active ( active = not retracted )
def test_that_internal_search_for_active_subsystems_correctly_excludes_retracted_subsystems(
    retraction_states: list[bool], active_subsystem_in_list: int | None
) -> None:
    # set up test conditions
    mock_subsystems = _given_a_set_of_subsystems_retracted_per_these_states(
        retraction_states=retraction_states
    )
    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(*mock_subsystems)
    amp_example: AttenuatorMotorPositions = AttenuatorMotorPositions(
        continuous_positions={"x": -12.2, "y": 31.779}, discrete_indices={"u": 4}
    )

    # stress the method on trial
    report: list[AttenuatorTeam] = (
        attenuation_system._find_active_susbsystems_if_motors_were_at(
            motor_positions=amp_example
        )
    )

    # assert sentinel mock survives filtering search or doesn't as per test parameters
    if (
        active_subsystem_in_list is not None
    ):  # have to remember zero is considered false in C / Python
        assert len(report) == 1  # assert survivor was unique
        assert (
            report[0] is mock_subsystems[active_subsystem_in_list]
        )  # assert sentinel mock came through the search
    else:
        assert len(report) < 1  # or else assert anticipated blank result from search


@pytest.mark.parametrize(
    "bn_per_subsystem, retraction_states,expected_total_bn",
    [
        (345.82, [True], CANONICAL_NON_ABSORPTION),
        (561.4, [True, False], 561.4),
        (2200, [False, True], 2200),
        (1150.7, [True, True], CANONICAL_NON_ABSORPTION),
        (978.31663, [False], 978.31663),
    ],
)
# Note: On the happy path - either zero or one subsystem is active ( active = not retracted )
def test_that_attenuation_prediction_is_based_on_subsystem_reports_of_attenuation_and_retraction_state(
    bn_per_subsystem: float,
    retraction_states: list[bool],
    expected_total_bn,
) -> None:

    # factory for churning out mocked instances
    def _mocked_out_subsystem(
        *, retraction_state: bool, attenuation_bn: float
    ) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.is_retracted_at.return_value = retraction_state
        mocked_subsystem.predict_attenuation_at.return_value = attenuation_bn
        return mocked_subsystem

    # set up test resources
    mocked_subsystems: list[AsyncMock] = [
        _mocked_out_subsystem(retraction_state=r, attenuation_bn=bn_per_subsystem)
        for r in retraction_states
    ]
    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(*mocked_subsystems)

    # stress the method on trial
    reported_bn: float = attenuation_system.predict_attenuation_bn_at(
        energy_kev=21398.47,  # arbitrary and irrelevant here
        motor_positions=AttenuatorMotorPositions(),
    )
    assert reported_bn == pytest.approx(expected=expected_total_bn)


@pytest.mark.parametrize("strictness", [True, False])
async def test_that_current_attenuation_request_bases_estimate_on_motor_position_readings(
    strictness: bool,
) -> None:

    # prepare tested state
    strut_motor_positions1 = AsyncMock(spec=AttenuatorMotorPositions)
    strut_motor_positions2 = AsyncMock(spec=AttenuatorMotorPositions)

    sentinel_motor_positions = AsyncMock(spec=AttenuatorMotorPositions)
    strut_motor_positions1.__or__.return_value = sentinel_motor_positions

    mocked_primary = AsyncMock(spec=AttenuatorTeam)
    mocked_primary.is_retracted_at.return_value = True
    mocked_primary.current_motor_positions.return_value = strut_motor_positions1

    mocked_secondary = AsyncMock(spec=AttenuatorTeam)
    mocked_secondary.is_retracted_at.return_value = False
    mocked_secondary.current_motor_positions.return_value = strut_motor_positions2  # not strictly needed here - but symmetry is easier to read

    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(
        mocked_primary, mocked_secondary
    )
    subsystems: list[AsyncMock] = [mocked_primary, mocked_secondary]

    # verify lack of false positives in later call checking
    for s in subsystems:
        s.current_motor_positions.assert_not_awaited()
    mocked_secondary.predict_attenuation_at.assert_not_called()

    # exercise the method under trial
    _discarded_attenuation_reading = (
        await attenuation_system.read_system_attenuation_bn(
            energy_kev=12.345, strict=strictness
        )
    )

    # verify the expected internal consequences
    for s in subsystems:
        s.current_motor_positions.assert_awaited_once()
    mocked_secondary.predict_attenuation_at.assert_called_once_with(
        energy_kev=12.345, hypothetical_motor_positions=sentinel_motor_positions
    )


@pytest.mark.parametrize(
    "bn_per_subsystem, retraction_states, expected_total_bn",
    [
        (845.82, [True], CANONICAL_NON_ABSORPTION),
        (501.4, [True, False], 501.4),
        (1607, [False, True], 1607),
        (1250.3, [True, True], CANONICAL_NON_ABSORPTION),
        (975.31663, [False], 975.31663),
    ],
)
# Note: On the happy path - either zero or one subsystem is active ( active = not retracted )
async def test_that_current_attenuation_report_is_based_on_subsystem_reports_of_attenuation_and_retraction_state(
    bn_per_subsystem: float,
    retraction_states: list[bool],
    expected_total_bn,
) -> None:

    # factory for churning out mocked subsystems
    def _mocked_out_subsystem(
        *, retraction_state: bool, attenuation_bn: float
    ) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.is_retracted_at.return_value = retraction_state
        mocked_subsystem.predict_attenuation_at.return_value = attenuation_bn
        return mocked_subsystem

    # mock subsystem delegates with prepared retraction states and attenuations
    mocked_subsystems: list[AsyncMock] = [
        _mocked_out_subsystem(retraction_state=r, attenuation_bn=bn_per_subsystem)
        for r in retraction_states
    ]
    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(*mocked_subsystems)

    # stress the method on trial
    reported_bn: float = await attenuation_system.read_system_attenuation_bn(
        energy_kev=15322.9,  # arbitrary and irrelevant here
    )
    assert reported_bn == pytest.approx(expected_total_bn)


@pytest.mark.parametrize(
    "subsystem_responses, expected_solution",
    [
        (
            [
                (True, {"y": 54.3}, {"w": 2}, {"y": -8.2}, {"w": 1}),
                (False, {"x": 15.88}, {}, {"x": -4.9}, {}),
            ],
            {"w": 2, "x": -4.9, "y": 54.3},
        ),
        (
            [
                (False, {"y": 44.91}, {"w": 5}, {"y": -18.2}, {"w": 1}),
                (True, {"x": 35.48}, {}, {"x": -7.2}, {}),
            ],
            {"w": 1, "x": 35.48, "y": -18.2},
        ),
        (
            [
                (False, {"y": 44.91}, {"w": 5}, {"y": -12.2}, {"w": 4}),
                (False, {"x": 35.48}, {}, {"x": -3.2}, {}),
            ],
            {"w": 4, "x": -3.2, "y": -12.2},
        ),
    ],
)
async def test_that_swiftest_motor_shift_solution_is_faithful_to_subsystem_reports(
    subsystem_responses: list[
        tuple[
            bool,  # can the subsystem accommodate the requested attenuation demand
            dict[
                PermittedKeyStr, float
            ],  # a hypothetical active position for the subsystem wedge(s)
            dict[
                PermittedKeyStr, int
            ],  # a hypothetical active index for the subsystem wheel(s) - if it even has a wheel
            dict[
                PermittedKeyStr, float
            ],  # a hypothetical retracted position for the subsystem wedge
            dict[
                PermittedKeyStr, int
            ],  # a hypothetical retracted index for the subsystem wheel(s) - if it has any wheels
        ]
    ],
    expected_solution: dict[PermittedKeyStr, float | int],
) -> None:

    # factory for churning out mocked subsystems
    def _mocked_out_subsystem(
        *,
        can_accommodate_demand: bool,
        active_motor_position: AttenuatorMotorPositions,
        retracted_motor_position: AttenuatorMotorPositions,
    ) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.can_accommodate.return_value = can_accommodate_demand
        if can_accommodate_demand:
            mocked_subsystem.solve_swiftest_motor_shift.return_value = (
                active_motor_position
            )
            mocked_subsystem.merge_in_retraction_motor_positions.side_effect = lambda: (
                pytest.fail("FAIL: Tested code makes unexpected call.")
            )
        else:
            mocked_subsystem.merge_in_retraction_motor_positions.side_effect = (
                lambda *, other_motor_positions: (
                    retracted_motor_position | other_motor_positions
                )
            )
            mocked_subsystem.solve_swiftest_motor_shift.side_effect = lambda: (
                pytest.fail("FAIL: Tested code makes unexpected call.")
            )
        return mocked_subsystem

    # mock subsystem delegates with state prepared according to specific test parametrisation
    mocked_subsystems: list[AsyncMock] = [
        _mocked_out_subsystem(
            can_accommodate_demand=able_to,  # True here means this subsystem claims it can meet the demanded attenuation
            active_motor_position=(
                AttenuatorMotorPositions(
                    continuous_positions=active_wedge_positions,
                    discrete_indices=active_wheel_indices,
                )
            ),
            retracted_motor_position=(
                AttenuatorMotorPositions(
                    continuous_positions=retracted_wedge_positions,
                    discrete_indices=retracted_wheel_indices,
                )
            ),
        )
        for (
            able_to,
            active_wedge_positions,
            active_wheel_indices,
            retracted_wedge_positions,
            retracted_wheel_indices,
        ) in subsystem_responses
    ]
    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(*mocked_subsystems)

    # prepare dummy args for the call on trial
    dummy_demand_bn = 1675.48201
    dummy_energy_kev = 12.8915
    dummy_starting_positions = AttenuatorMotorPositions(
        discrete_indices={"w": 6}, continuous_positions={"x": 27.1, "y": -4.8}
    )

    # stress the method on trial
    soln: AttenuatorMotorPositions = attenuation_system.solve_for_swiftest_motor_shift(
        attenuation_demand_bn=dummy_demand_bn,
        energy_kev=dummy_energy_kev,
        starting_positions=dummy_starting_positions,
    )
    # validate that reported solution meets expectations
    assert soln.validated_and_complete == expected_solution


@pytest.mark.parametrize(
    "subsystem_responses, expected_solution",
    [
        (
            [
                ({"y": 64.3}, {"w": 4}, {"y": -8.2}, {"w": 6}),
                ({"x": 15.88}, {}, {"x": -5.9}, {}),
            ],
            {"w": 4, "x": -5.9, "y": 64.3},
        ),
        (
            [
                ({"y": 41.91}, {"w": 5}, {"y": -18.2}, {"w": 1}),
                ({"x": 35.48}, {}, {"x": -7.2}, {}),
            ],
            {"w": 5, "x": -7.2, "y": 41.91},
        ),
        # note the order of subsystems is swapped for the rest of this set of tests
        (
            [
                ({"x": 15.88}, {}, {"x": -5.9}, {}),
                ({"y": 64.3}, {"w": 4}, {"y": -8.2}, {"w": 6}),
            ],
            {"w": 6, "x": 15.88, "y": -8.2},
        ),
        (
            [
                ({"x": 35.48}, {}, {"x": -7.2}, {}),
                ({"y": 41.91}, {"w": 5}, {"y": -18.2}, {"w": 1}),
            ],
            {"w": 1, "x": 35.48, "y": -18.2},
        ),
    ],
)
async def test_that_swiftest_motor_shift_solution_uses_earliest_available_subsystem_even_if_both_can_accommodate_demanded_attenuation(
    subsystem_responses: list[
        tuple[
            dict[
                PermittedKeyStr, float
            ],  # a hypothetical active position for the subsystem wedge(s)
            dict[
                PermittedKeyStr, int
            ],  # a hypothetical active index for the subsystem wheel(s) - if it even has a wheel
            dict[
                PermittedKeyStr, float
            ],  # a hypothetical retracted position for the subsystem wedge
            dict[
                PermittedKeyStr, int
            ],  # a hypothetical retracted index for the subsystem wheel(s) - if it has any wheels
        ]
    ],
    expected_solution: dict[PermittedKeyStr, float | int],
) -> None:

    def _convert_test_parameters_to_attenuator_motor_position_kwargs(
        active_wedge_positions: dict[
            PermittedKeyStr, float
        ],  # a hypothetical active position for the subsystem wedge(s)
        active_wheel_indices: dict[
            PermittedKeyStr, int
        ],  # a hypothetical active index for the subsystem wheel(s) - if it even has a wheel
        retracted_wedge_positions: dict[
            PermittedKeyStr, float
        ],  # a hypothetical retracted position for the subsystem wedge
        retracted_wheel_indices: dict[PermittedKeyStr, int],
    ) -> dict[str, AttenuatorMotorPositions]:
        return {
            "active_motor_position": AttenuatorMotorPositions(
                continuous_positions=active_wedge_positions,
                discrete_indices=active_wheel_indices,
            ),
            "retracted_motor_position": AttenuatorMotorPositions(
                continuous_positions=retracted_wedge_positions,
                discrete_indices=retracted_wheel_indices,
            ),
        }

    # factory for churning out mocked subsystems
    def _mocked_out_subsystem(
        *,
        active_motor_position: AttenuatorMotorPositions,
        retracted_motor_position: AttenuatorMotorPositions,
    ) -> AsyncMock:
        mocked_subsystem = AsyncMock(spec=AttenuatorTeam)
        mocked_subsystem.can_accommodate.return_value = True
        mocked_subsystem.solve_swiftest_motor_shift.return_value = active_motor_position
        mocked_subsystem.merge_in_retraction_motor_positions.side_effect = (
            lambda *, other_motor_positions: (
                retracted_motor_position | other_motor_positions
            )
        )
        return mocked_subsystem

    # mock subsystem delegates with state prepared according to specific test parametrisation
    mocked_subsystems: list[AsyncMock] = [
        _mocked_out_subsystem(
            **_convert_test_parameters_to_attenuator_motor_position_kwargs(
                active_wedge_positions,
                active_wheel_indices,
                retracted_wedge_positions,
                retracted_wheel_indices,
            )
        )
        for (
            active_wedge_positions,
            active_wheel_indices,
            retracted_wedge_positions,
            retracted_wheel_indices,
        ) in subsystem_responses
    ]
    # build class on trial using prepared mocks
    attenuation_system: AttenuationSystem = AttenuationSystem(*mocked_subsystems)

    # prepare dummy args for the call on trial
    dummy_demand_bn = 1705.4301
    dummy_energy_kev = 18.615
    dummy_starting_positions = AttenuatorMotorPositions(
        discrete_indices={"w": 3}, continuous_positions={"x": 17.1, "y": -4.78}
    )

    # stress the method on trial
    soln: AttenuatorMotorPositions = attenuation_system.solve_for_swiftest_motor_shift(
        attenuation_demand_bn=dummy_demand_bn,
        energy_kev=dummy_energy_kev,
        starting_positions=dummy_starting_positions,
    )
    # validate that reported solution meets expectations
    assert soln.validated_and_complete == expected_solution
