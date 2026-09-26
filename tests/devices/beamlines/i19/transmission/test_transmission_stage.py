
from typing import Final, cast
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorSquad,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.attenuation_system import (
    AttenuationSystem,
)
from dodal.devices.beamlines.i19.transmission.transmission_api import (
    Transmission,
    TransmissionAPI,
)
from dodal.devices.beamlines.i19.transmission.transmission_stage import (
    TransmissionStage,
)

EXAMPLE_ATTENUATION_BN: Final[list[float]] = [
    CANONICAL_NON_ABSORPTION, 22.8, 306.40194234, 1219.5134985, 2893.042463
]

EXAMPLE_TRANSMISSION_VALUES: Final[list[Transmission]] = [
    1, 0.825, 0.71, 0.64, 0.503, 0.48, 0.37, 0.32, 0.25, 0.18, 0.07,
]

EXAMPLE_X_RAY_ENERGIES: Final[list[float]] = [
    2.3, 5.6, 7.81, 10.39, 12.452, 15.6, 19.87, 23.5, 26.7,
]

# Auxiliary methods below

def _build_a_fake_motor_squad() -> AttenuatorMotorSquad:
    mock_squad = AsyncMock(spec=AttenuatorMotorSquad)
    mock_squad.set = AsyncMock()  # needed to overcome AsyncStatus.wrap blindspot
    return cast(AttenuatorMotorSquad, mock_squad)


def _build_tx_stage_where_mocked_delegate_predicts_attenuation() -> tuple[
        TransmissionStage, MagicMock
]:
    fake_delegate_attenuation_system = MagicMock(autospec=AttenuationSystem)
    strut_motor_squad = _build_a_fake_motor_squad()
    tx_stage = TransmissionStage(
        tx_stage_name="DummyStageTypeI",
        motors_squad=strut_motor_squad,
        attenuation_system=fake_delegate_attenuation_system,
    )
    return tx_stage, fake_delegate_attenuation_system.predict_attenuation_bn_at


def _build_tx_stage_where_mocked_delegate_solves_motor_shift() -> tuple[
        TransmissionStage, MagicMock,
]:
    fake_delegate_attenuation_system = MagicMock(autospec=AttenuationSystem)
    fake_delegate_attenuation_system.get_current_motor_positions = AsyncMock()  # MagicMock assumes sync methods
    strut_motor_squad = _build_a_fake_motor_squad()
    tx_stage = TransmissionStage(
        tx_stage_name="DummyStageTypeII",
        motors_squad=strut_motor_squad,
        attenuation_system=fake_delegate_attenuation_system,
    )
    return tx_stage, fake_delegate_attenuation_system.solve_for_swiftest_motor_shift


def _once_tx_stage_predicts_transmission(
    tx_stage: TransmissionStage,
    *,
    energy_kev: float,
    motor_positions: AttenuatorMotorPositions,
) -> Transmission:
    return tx_stage.predict_transmission_at(
        energy_kev=energy_kev, motor_positions=motor_positions
    )


def _once_tx_stage_solves_for_swiftest_motor_shift(
    tx_stage: TransmissionStage,
    *,
    tx_demand: Transmission,
    energy_kev: float,
    prior_positions: AttenuatorMotorPositions,
) -> AttenuatorMotorPositions:
    return tx_stage.solve_for_swiftest_motor_shift(
        transmission_demand=tx_demand,
        energy_kev=energy_kev,
        starting_positions=prior_positions,
    )

# tests below

def test_that_transmission_stage_syntactically_upholds_transmission_api() -> None:
    tx_stage = TransmissionStage(
            tx_stage_name="DummyStage",
            motors_squad=_build_a_fake_motor_squad(),
            attenuation_system=MagicMock(autospec=AttenuationSystem),
        )
    assert isinstance(tx_stage, TransmissionAPI)


@pytest.mark.parametrize(
    "example_energy_kev",
    EXAMPLE_X_RAY_ENERGIES,
)
@pytest.mark.parametrize(
    "example_tx",
    EXAMPLE_TRANSMISSION_VALUES,
)
async def test_that_driving_transmission_update_requests_position_solution(example_energy_kev: float,
                                                                           example_tx: Transmission) -> None:
    fake_delegate_attenuation_system = MagicMock(autospec=AttenuationSystem)
    fake_delegate_attenuation_system.get_current_motor_positions = (
        AsyncMock(return_value=AttenuatorMotorPositions())  # MagicMock assumes sync methods
    )
    strut_motor_squad = _build_a_fake_motor_squad()
    stage = TransmissionStage(
        tx_stage_name="TxStage",
        motors_squad=strut_motor_squad,
        attenuation_system=fake_delegate_attenuation_system,
    )
    mock_solver_on_delegate = fake_delegate_attenuation_system.solve_for_swiftest_motor_shift
    mock_solver_on_delegate.assert_not_called()
    sentinel_start_position = AttenuatorMotorPositions(continuous_positions={"y": 12.6,"x": 55.1},
                                                       discrete_indices={"w": 4})
    await stage.drive_transmission_to(transmission_demand=example_tx,
                                      energy_kev=example_energy_kev,
                                      starting_positions=sentinel_start_position)
    mock_solver_on_delegate.assert_called_once_with(attenuation_demand_bn=ANY,
                                                    energy_kev=example_energy_kev,
                                                    starting_positions=sentinel_start_position)


@pytest.mark.parametrize(
    "example_energy_kev",
    EXAMPLE_X_RAY_ENERGIES,
)
@pytest.mark.parametrize(
    "example_tx",
    EXAMPLE_TRANSMISSION_VALUES,
)
async def test_that_driving_transmission_update_applies_solution_found(example_energy_kev: float,
                                                                       example_tx: Transmission) -> None:
    fake_delegate_attenuation_system = MagicMock(autospec=AttenuationSystem)
    fake_delegate_attenuation_system.get_current_motor_positions = (
        AsyncMock(return_value=AttenuatorMotorPositions())  # MagicMock assumes sync methods
    )
    strut_motor_squad = _build_a_fake_motor_squad()
    strut_motor_squad.set = AsyncMock()  # overcomes blind spot created by AsyncStatus.wrap decoration
    stage = TransmissionStage(
        tx_stage_name="TxStage",
        motors_squad=strut_motor_squad,
        attenuation_system=fake_delegate_attenuation_system,
    )
    mock_solver_on_delegate = fake_delegate_attenuation_system.solve_for_swiftest_motor_shift
    sentinel_position_solution = AttenuatorMotorPositions(continuous_positions={"y": 12.6,"x": 55.1},
                                                       discrete_indices={"w": 4})
    mock_solver_on_delegate.return_value = sentinel_position_solution
    await stage.drive_transmission_to(transmission_demand=example_tx,
                                      energy_kev=example_energy_kev,
                                      starting_positions=AttenuatorMotorPositions())
    spy_motor_setter = cast(AsyncMock, stage.access_controlled_motors.set)
    spy_motor_setter.assert_awaited_once_with(value=sentinel_position_solution)


async def test_that_request_to_read_motor_positions_reports_result_from_subsystems() -> None:
    mock_atten_system = AsyncMock(autospec=AttenuationSystem)
    sentinel = AttenuatorMotorPositions()
    mock_atten_system.get_current_motor_positions.return_value = sentinel

    tx_stage: TransmissionAPI = TransmissionStage(
        tx_stage_name="TxStage",
        motors_squad=_build_a_fake_motor_squad(),
        attenuation_system=mock_atten_system,
    )
    # prove delegate internal system has not yet been called
    mock_atten_system.get_current_motor_positions.assert_not_awaited()
    # invoke API read on tx stage
    result = await tx_stage.read_current_motor_positions()
    # confirm this invokes the delegate method
    mock_atten_system.get_current_motor_positions.assert_awaited_once()
    # confirm delegate result has bubbled up to be the outer read output
    assert result is sentinel


@pytest.mark.parametrize(
    "sentinel_kev",
    EXAMPLE_X_RAY_ENERGIES,
)
def test_when_transmission_prediction_sought_that_tx_stage_passes_energy_kev_to_attenuation_system_predictor(
    sentinel_kev,
):
    stage, mock_predictor_on_delegate = _build_tx_stage_where_mocked_delegate_predicts_attenuation()
    mock_predictor_on_delegate.assert_not_called()
    _once_tx_stage_predicts_transmission(
        stage, energy_kev=sentinel_kev, motor_positions=AttenuatorMotorPositions(),
    )
    mock_predictor_on_delegate.assert_called_once_with(
        energy_kev=sentinel_kev, motor_positions=ANY
    )


@pytest.mark.parametrize(
    "wedge_positions, wheel_indices",
    [
        ({"y": 93.3}, {}),
        ({}, {}),
        ({"y": 15.2, "x": -1.05}, {"w": 1}),
        ({"y": 19.81}, {"w": 3}),
        ({"x": 13.04, "y": 26.5}, {}),
    ],
)
def test_when_transmission_prediction_sought_that_tx_stage_passes_starting_motor_positions_to_attenuation_system_predictor(
    wedge_positions: dict[str,float],
    wheel_indices: dict[str, int],
):
    stage, mock_predictor_on_delegate = _build_tx_stage_where_mocked_delegate_predicts_attenuation()
    mock_predictor_on_delegate.assert_not_called()
    sentinel_motor_positions = AttenuatorMotorPositions(continuous_positions=wedge_positions,
                                                        discrete_indices=wheel_indices)
    _once_tx_stage_predicts_transmission(
        stage, energy_kev=12.3456, motor_positions=sentinel_motor_positions
    )
    mock_predictor_on_delegate.assert_called_once_with(
        energy_kev=12.3456, motor_positions=sentinel_motor_positions
    )

@pytest.mark.parametrize(
    "sentinel_tx",
    EXAMPLE_TRANSMISSION_VALUES
)
@pytest.mark.parametrize(
    "example_bn",
    EXAMPLE_ATTENUATION_BN
)
@patch(
    "dodal.devices.beamlines.i19.transmission.transmission_stage.transmission_from_attenuation",
    autospec=True,
)
async def test_when_system_transmission_read_that_system_attenuation_is_converted_to_transmission(
    patched_convertor: MagicMock,
    example_bn: float,
    sentinel_tx: Transmission
):
    strut_atten_system = AsyncMock(autospec=AttenuationSystem)
    tx_stage: TransmissionAPI = TransmissionStage(
            tx_stage_name="TxStage",
            motors_squad=_build_a_fake_motor_squad(),
            attenuation_system=strut_atten_system,
    )
    strut_atten_system.read_system_attenuation_bn.return_value = example_bn
    patched_convertor.return_value = sentinel_tx
    result = await tx_stage.read_current_system_transmission(energy_kev=13.2478)
    patched_convertor.assert_called_once_with(example_bn)
    assert result is sentinel_tx


@pytest.mark.parametrize(
    "example_kev",
    EXAMPLE_X_RAY_ENERGIES
)
async def test_when_system_transmission_read_that_system_attenuation_is_requested(example_kev: float):
    mock_atten_system = AsyncMock(autospec=AttenuationSystem)
    tx_stage: TransmissionAPI = TransmissionStage(
            tx_stage_name="TxStage",
            motors_squad=_build_a_fake_motor_squad(),
            attenuation_system=mock_atten_system,
    )
    mock_atten_system.read_system_attenuation_bn.assert_not_awaited()
    await tx_stage.read_current_system_transmission(energy_kev=example_kev)
    mock_atten_system.read_system_attenuation_bn.assert_awaited_once()


@pytest.mark.parametrize(
    "sentinel_attenuation",
    EXAMPLE_ATTENUATION_BN,
)
@patch(
    "dodal.devices.beamlines.i19.transmission.transmission_stage.attenuation_from_transmission",
    autospec=True,
)
def test_when_motor_solution_sought_that_tx_stage_passes_attenuation_demand_to_delegate(
    patched_convertor: MagicMock,
    sentinel_attenuation: float
) -> None:
    stage, mock_solver_on_delegate = (
        _build_tx_stage_where_mocked_delegate_solves_motor_shift()
    )
    patched_convertor.return_value = sentinel_attenuation
    _once_tx_stage_solves_for_swiftest_motor_shift(
        stage,
        tx_demand=0.5,
        energy_kev=11.6781,
        prior_positions=AttenuatorMotorPositions(),
    )
    mock_solver_on_delegate.assert_called_once_with(
        attenuation_demand_bn=sentinel_attenuation,
        energy_kev=ANY,
        starting_positions=ANY,
    )


@pytest.mark.parametrize(
    "example_tx",
    EXAMPLE_TRANSMISSION_VALUES,
)
@pytest.mark.parametrize(
    "sentinel_kev",
    EXAMPLE_X_RAY_ENERGIES,
)
def test_when_motor_solution_sought_that_tx_stage_passes_x_ray_energy_through_to_delegate(
    sentinel_kev: float,
    example_tx: Transmission,
) -> None:
    stage, mock_solver_on_delegate = (
        _build_tx_stage_where_mocked_delegate_solves_motor_shift()
    )
    _once_tx_stage_solves_for_swiftest_motor_shift(
        stage,
        tx_demand=example_tx,
        energy_kev=sentinel_kev,
        prior_positions=AttenuatorMotorPositions(),
    )
    mock_solver_on_delegate.assert_called_once()


@pytest.mark.parametrize(
    "wedge_positions, wheel_indices",
    [
        ({"y": 93.3}, {}),
        ({}, {"v": 5}),
        ({}, {}),
        ({"y": 15.2, "x": -1.05}, {"w": 1}),
        ({"x": 19.81}, {"w": 3}),
        ({"y": 25.6}, {"v": 4, "w": 3}),
        ({"x": 13.04, "y": 26.5}, {}),
    ],
)
@patch(
    "dodal.devices.beamlines.i19.transmission.transmission_stage.attenuation_from_transmission",
    autospec=True,
)
def test_when_motor_solution_sought_that_tx_stage_passes_starting_positions_through_to_delegate(
    patched_convertor: MagicMock,
    wedge_positions: dict[str, float],
    wheel_indices: dict[str, int],
) -> None:
    stage, mock_solver_on_delegate = (
        _build_tx_stage_where_mocked_delegate_solves_motor_shift()
    )
    patched_convertor.return_value = ANY
    sentinel_motor_starting_positions = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_indices,
    )
    _once_tx_stage_solves_for_swiftest_motor_shift(
        stage,
        tx_demand=0.2,
        energy_kev=19.8143,
        prior_positions=sentinel_motor_starting_positions,
    )
    mock_solver_on_delegate.assert_called_once_with(
        attenuation_demand_bn=ANY,
        energy_kev=ANY,
        starting_positions=sentinel_motor_starting_positions,
    )


@pytest.mark.parametrize(
    "example_tx",
    EXAMPLE_TRANSMISSION_VALUES,
)
@patch(
    "dodal.devices.beamlines.i19.transmission.transmission_stage.transmission_from_attenuation",
    autospec=True,
)
def test_that_tx_stage_passes_motor_shift_solution_up_from_delegate_attenuation_system(
    mock_convertor: MagicMock,
    example_tx: Transmission,
):
    mock_convertor.return_value = 0.64  # exact transmission value unimportant in this test

    fake_delegate_attenuation_system = MagicMock(autospec=AttenuationSystem)
    dummy_motor_starting_point: AttenuatorMotorPositions = AttenuatorMotorPositions()
    sentinel_motor_solution: AttenuatorMotorPositions = AttenuatorMotorPositions(
        continuous_positions={"x": 88.4}, discrete_indices={"w": 2}
    )
    fake_delegate_attenuation_system.solve_for_swiftest_motor_shift = MagicMock(
        return_value=sentinel_motor_solution
    )
    stage = TransmissionStage(
        tx_stage_name="DummyStage",
        motors_squad=AsyncMock(autospec=True),
        attenuation_system=fake_delegate_attenuation_system,
    )

    result = _once_tx_stage_solves_for_swiftest_motor_shift(
        stage, tx_demand=example_tx, energy_kev=23.045, prior_positions=dummy_motor_starting_point
    )
    assert result is sentinel_motor_solution


# TODO - add unhappy path testing
