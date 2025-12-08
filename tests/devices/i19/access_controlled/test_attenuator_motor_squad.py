from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.client import ClientConnectionError
from bluesky.run_engine import RunEngine

from dodal.devices.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositionDemands,
    AttenuatorMotorSquad,
)
from dodal.devices.i19.access_controlled.blueapi_device import HutchState


def given_position_demands() -> AttenuatorMotorPositionDemands:
    position_demand = MagicMock()
    restful_payload = {"x": 54.3, "y": 72.1, "w": 4}
    position_demand.validated_complete_demand = MagicMock(return_value=restful_payload)
    return position_demand


def given_an_unhappy_restful_response(*args: Any, **kwargs: Any) -> AsyncMock:
    unhappy_response = AsyncMock()
    unhappy_response.ok = False
    unhappy_response.json = AsyncMock(
        return_value={"task_id": "unhappy_response_intended"}
    )
    return unhappy_response


async def given_a_squad_of_attenuator_motors(
    hutch: HutchState,
) -> AttenuatorMotorSquad:
    motor_squad = AttenuatorMotorSquad(
        hutch, instrument_session="cm54321-0", name="attenuator_motor_squad"
    )
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
    "dodal.devices.i19.access_controlled.attenuator_motor_squad.OpticsBlueAPIDevice.set",
    new_callable=AsyncMock,
)
async def test_when_motor_squad_is_set_that_expected_request_params_are_passed(
    internal_setter, invoking_hutch: HutchState
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
    expected_instrument_session: str = "cm54321-0"
    expected_request: dict = {
        "name": expected_request_name,
        "params": expected_parameters,
        "instrument_session": expected_instrument_session,
    }
    internal_setter.assert_called_once_with(expected_request)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
async def test_that_set_raises_error_if_post_not_successful(
    invoking_hutch: HutchState,
):
    position_demands = given_position_demands()
    motors: AttenuatorMotorSquad = await given_a_squad_of_attenuator_motors(
        invoking_hutch
    )
    with pytest.raises(ClientConnectionError):
        with patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.post"
        ) as mock_post:
            mock_post.return_value.__aenter__.return_value = (
                given_an_unhappy_restful_response()
            )

            await motors.set(position_demands)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
@patch("dodal.devices.i19.access_controlled.blueapi_device.LOGGER")
@patch("dodal.devices.i19.access_controlled.blueapi_device.ClientSession.put")
@patch("dodal.devices.i19.access_controlled.blueapi_device.ClientSession.post")
async def test_that_error_is_logged_when_response_to_position_demand_set_indicates_failure(
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
