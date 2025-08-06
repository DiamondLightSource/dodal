from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client import ClientConnectionError
from bluesky.run_engine import RunEngine

from dodal.devices.i19.access_controlled.attenuator_motor_set import (
    AttenuatorMotorSet,
    AttenuatorPositionDemand,
)
from dodal.devices.i19.access_controlled.optics_blueapi_device import HutchState


def given_a_position_demand() -> AttenuatorPositionDemand:
    wedge_demands = {"x": 54.3, "y": 72.1}
    wheel_demands = {"w": 4}
    return AttenuatorPositionDemand(wedge_demands, wheel_demands)


def given_an_unhappy_restful_response() -> AsyncMock:
    unhappy_response = AsyncMock()
    unhappy_response.ok = False
    unhappy_response.json.return_value = {"task_id": "alas_not"}
    return unhappy_response


def given_a_blank_device_pv_prefix():
    return ""


async def given_set_of_attenuator_motors(hutch: HutchState) -> AttenuatorMotorSet:
    prefix = given_a_blank_device_pv_prefix()
    motor_set = AttenuatorMotorSet(prefix, hutch, name="fake_motor_set")
    await motor_set.connect(mock=True)

    motor_set.url = "http://test-blueapi.url"
    return motor_set


@pytest.fixture
async def eh1_motor_set(RE: RunEngine) -> AttenuatorMotorSet:
    return await given_set_of_attenuator_motors(HutchState.EH1)


@pytest.fixture
async def eh2_motor_set(RE: RunEngine) -> AttenuatorMotorSet:
    return await given_set_of_attenuator_motors(HutchState.EH2)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
async def test_that_motor_set_can_be_instantiated(invoking_hutch: HutchState):
    motor_set: AttenuatorMotorSet = await given_set_of_attenuator_motors(invoking_hutch)
    assert isinstance(motor_set, AttenuatorMotorSet)  # could have been None


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
async def test_when_rest_post_unsuccessful_that_error_raised(
    invoking_hutch: HutchState,
):
    motors: AttenuatorMotorSet = await given_set_of_attenuator_motors(invoking_hutch)
    restful_post: str = (
        "dodal.devices.i19.access_controlled.optics_blueapi_device.ClientSession.post"
    )
    with pytest.raises(ClientConnectionError):
        with patch(restful_post) as unsuccessful_post:
            restful_response: AsyncMock = given_an_unhappy_restful_response()
            unsuccessful_post.return_value.__aenter__.return_value = restful_response

            postion_demand = given_a_position_demand()
            await motors.set(postion_demand)


@pytest.mark.parametrize("invoking_hutch", [HutchState.EH1, HutchState.EH2])
async def test_that_error_is_logged_whenever_position_demand_fails(invoking_hutch):
    blue_api_stem: str = "dodal.devices.i19.access_controlled.optics_blueapi_device"
    logger: str = f"{blue_api_stem}.LOGGER"
    restful_template: str = f"{blue_api_stem}.ClientSession"
    restful_post: str = f"{restful_template}.post"
    restful_put: str = f"{restful_template}.put"
    with (
        patch(logger) as patched_logger,
        patch(restful_post) as fake_post,
        patch(restful_put) as fake_put,
    ):
        response_to_post: AsyncMock = AsyncMock()
        response_to_post.ok = True
        response_to_post.json.return_value = {"task_id": "0123"}
        fake_post.return_value.__aenter__.return_value = response_to_post

        response_to_put = AsyncMock()
        response_to_put.ok = False
        fake_put.return_value.__aenter__.return_value = response_to_put

        motors: AttenuatorMotorSet = await given_set_of_attenuator_motors(
            invoking_hutch
        )
        demand: AttenuatorPositionDemand = given_a_position_demand()

        patched_logger.error.assert_not_called()
        await motors.set(demand)
        patched_logger.error.assert_called_once()
