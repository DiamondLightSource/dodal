from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.client import ClientConnectionError
from bluesky.run_engine import RunEngine
from dodal.devices.i19.access_controlled.optics_blueapi_device import HutchState

from dodal.devices.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositionDemands,
    AttenuatorMotorSquad,
)


def given_position_demands() -> AttenuatorMotorPositionDemands:
    position_demand = MagicMock()
    restful_payload = {"x": 54.3, "y": 72.1, "w": 4}
    position_demand.restful_format = MagicMock(return_value=restful_payload)
    return position_demand


def given_an_unhappy_restful_response() -> AsyncMock:
    unhappy_response = AsyncMock()
    unhappy_response.ok = False
    unhappy_response.json.return_value = {"task_id": "alas_not"}
    return unhappy_response


async def given_a_squad_of_attenuator_motors(
    hutch: HutchState,
) -> AttenuatorMotorSquad:
    motor_squad = AttenuatorMotorSquad(hutch, name="attenuator_motor_squad")
    await motor_squad.connect(mock=True)

    motor_squad.url = "http://test-blueapi.url"
    return motor_squad


@pytest.fixture
async def eh1_motor_squad(re: RunEngine) -> AttenuatorMotorSquad:
    return await given_a_squad_of_attenuator_motors(HutchState.EH1)


@pytest.fixture
async def eh2_motor_squad(re: RunEngine) -> AttenuatorMotorSquad:
    return await given_a_squad_of_attenuator_motors(HutchState.EH2)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
async def test_that_motor_squad_can_be_instantiated(invoking_hutch):
    motor_squad: AttenuatorMotorSquad = await given_a_squad_of_attenuator_motors(
        invoking_hutch
    )
    assert isinstance(motor_squad, AttenuatorMotorSquad)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
@patch(
    "dodal.devices.i19.access_controlled.attenuator_motor_squad.OpticsBlueApiDevice.set",
    new_callable=AsyncMock,
)
async def test_when_motor_squad_is_set_that_expected_request_params_are_passed(
    internal_setter, invoking_hutch
):
    motors: AttenuatorMotorSquad = await given_a_squad_of_attenuator_motors(
        invoking_hutch
    )
    position_demands: AttenuatorMotorPositionDemands = given_position_demands()
    await motors.set(position_demands)  # when motor position demand is set

    expected_hutch: str = invoking_hutch.value
    expected_device: str = "access_control"
    expected_request_name: str = "operate_motor_squad_plan"
    expected_parameters: dict = {
        "experiment_hutch": expected_hutch,
        "access_device": expected_device,
        "attenuator_demands": {"x": 54.3, "y": 72.1, "w": 4},
    }
    expected_request: dict = {
        "name": expected_request_name,
        "params": expected_parameters,
    }
    internal_setter.assert_called_once_with(expected_request)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
@patch("dodal.devices.i19.access_controlled.optics_blueapi_device.ClientSession.post")
async def test_when_rest_post_unsuccessful_that_error_raised(
    unsuccessful_post, invoking_hutch
):
    motors: AttenuatorMotorSquad = await given_a_squad_of_attenuator_motors(
        invoking_hutch
    )
    with pytest.raises(ClientConnectionError):
        restful_response: AsyncMock = given_an_unhappy_restful_response()
        unsuccessful_post.return_value.__aenter__.return_value = restful_response

        postion_demands = given_position_demands()
        await motors.set(postion_demands)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
@patch("dodal.devices.i19.access_controlled.optics_blueapi_device.LOGGER")
@patch("dodal.devices.i19.access_controlled.optics_blueapi_device.ClientSession.put")
@patch("dodal.devices.i19.access_controlled.optics_blueapi_device.ClientSession.post")
async def test_that_error_is_logged_whenever_position_demand_fails(
    restful_post, restful_put, logger, invoking_hutch
):
    response_to_post: AsyncMock = AsyncMock()
    response_to_post.ok = True
    response_to_post.json.return_value = {"task_id": "0123"}
    restful_post.return_value.__aenter__.return_value = response_to_post

    response_to_put = AsyncMock()
    response_to_put.ok = False
    restful_put.return_value.__aenter__.return_value = response_to_put

    motors: AttenuatorMotorSquad = await given_a_squad_of_attenuator_motors(
        invoking_hutch
    )
    position_demands: AttenuatorMotorPositionDemands = given_position_demands()

    logger.error.assert_not_called()
    await motors.set(position_demands)
    logger.error.assert_called_once()
