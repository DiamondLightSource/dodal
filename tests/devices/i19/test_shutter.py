import json
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from aiohttp.client import ClientConnectionError
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.hutch_shutter import (
    ShutterDemand,
    ShutterState,
)
from dodal.devices.i19.blueapi_device import HEADERS, HutchState
from dodal.devices.i19.shutter import (
    AccessControlledShutter,
)


async def make_test_shutter(hutch: HutchState) -> AccessControlledShutter:
    shutter = AccessControlledShutter("", hutch, name="mock_shutter")
    await shutter.connect(mock=True)

    shutter.url = "http://test-blueapi.url"
    set_mock_value(shutter.shutter_status, ShutterState.CLOSED)
    return shutter


@pytest.fixture
async def eh1_shutter(RE: RunEngine) -> AccessControlledShutter:
    return await make_test_shutter(HutchState.EH1)


@pytest.fixture
async def eh2_shutter(RE: RunEngine) -> AccessControlledShutter:
    return await make_test_shutter(HutchState.EH2)


@pytest.mark.parametrize("hutch_name", [HutchState.EH1, HutchState.EH2])
def shutter_can_be_created_without_raising_errors(hutch_name: HutchState):
    test_shutter = AccessControlledShutter("", hutch_name, "test_shutter")
    assert isinstance(test_shutter, AccessControlledShutter)


async def test_read_on_eh1_shutter_device_returns_correct_status(
    eh1_shutter: AccessControlledShutter,
):
    reading = await eh1_shutter.read()
    assert reading == {
        "mock_shutter-shutter_status": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": ShutterState.CLOSED,
        }
    }


async def test_read_on_eh2_shutter_device_returns_correct_status(
    eh2_shutter: AccessControlledShutter,
):
    reading = await eh2_shutter.read()
    assert reading == {
        "mock_shutter-shutter_status": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": ShutterState.CLOSED,
        }
    }


async def test_set_raises_error_if_post_not_successful(
    eh2_shutter: AccessControlledShutter,
):
    with pytest.raises(ClientConnectionError):
        with patch("dodal.devices.i19.blueapi_device.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = (
                mock_response := AsyncMock()
            )
            mock_response.ok = False
            mock_response.json.return_value = {"task_id": "nope"}

            await eh2_shutter.set(ShutterDemand.OPEN)


@patch("dodal.devices.i19.blueapi_device.LOGGER")
async def test_no_task_id_returned_from_post(
    mock_logger: MagicMock, eh1_shutter: AccessControlledShutter
):
    with pytest.raises(KeyError):
        with (
            patch("dodal.devices.i19.blueapi_device.ClientSession.post") as mock_post,
        ):
            mock_post.return_value.__aenter__.return_value = (
                mock_response := AsyncMock()
            )
            mock_response.ok = True
            mock_response.json.return_value = {}

            await eh1_shutter.set(ShutterDemand.CLOSE)

            mock_logger.error.assert_called_once()


@pytest.mark.parametrize("shutter_demand", [ShutterDemand.OPEN, ShutterDemand.CLOSE])
async def test_set_corrently_makes_rest_calls(
    shutter_demand: ShutterDemand, eh2_shutter: AccessControlledShutter
):
    test_request = {
        "name": "operate_shutter_plan",
        "params": {
            "experiment_hutch": "EH2",
            "access_device": "access_control",
            "shutter_demand": shutter_demand.value,
        },
    }
    test_request_json = json.dumps(test_request)
    with (
        patch("dodal.devices.i19.blueapi_device.ClientSession.post") as mock_post,
        patch("dodal.devices.i19.blueapi_device.ClientSession.put") as mock_put,
        patch("dodal.devices.i19.blueapi_device.ClientSession.get") as mock_get,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": "1111"}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = True
        mock_get.return_value.__aenter__.return_value = (
            mock_get_response := AsyncMock()
        )
        mock_get_response.json.return_value = {"is_complete": True, "errors": []}

        await eh2_shutter.set(shutter_demand)

        mock_post.assert_called_with("/tasks", data=test_request_json, headers=HEADERS)
        mock_put.assert_called_with(
            "/worker/task", data='{"task_id": "1111"}', headers=HEADERS
        )


@patch("dodal.devices.i19.blueapi_device.LOGGER")
async def test_if_put_fails_log_error_and_return(
    mock_logger: MagicMock, eh1_shutter: AccessControlledShutter
):
    with (
        patch("dodal.devices.i19.blueapi_device.ClientSession.post") as mock_post,
        patch("dodal.devices.i19.blueapi_device.ClientSession.put") as mock_put,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": "0101"}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = False

        await eh1_shutter.set(ShutterDemand.OPEN)

        mock_logger.error.assert_called_once()


@patch("dodal.devices.i19.blueapi_device.LOGGER")
@patch("dodal.devices.i19.blueapi_device.asyncio.sleep")
async def test_if_plan_fails_raise_error_with_message(
    mock_sleep: MagicMock, mock_logger: MagicMock, eh2_shutter: AccessControlledShutter
):
    with pytest.raises(RuntimeError):
        with (
            patch("dodal.devices.i19.blueapi_device.ClientSession.post") as mock_post,
            patch("dodal.devices.i19.blueapi_device.ClientSession.put") as mock_put,
            patch("dodal.devices.i19.blueapi_device.ClientSession.get") as mock_get,
        ):
            mock_post.return_value.__aenter__.return_value = (
                mock_response := AsyncMock()
            )
            mock_response.ok = True
            mock_response.json.return_value = {"task_id": "0101"}
            mock_put.return_value.__aenter__.return_value = (
                mock_put_response := AsyncMock()
            )
            mock_put_response.ok = True
            mock_get.return_value.__aenter__.return_value = (
                mock_get_response := AsyncMock()
            )
            error_msg = "Oops, plan failed, couldn't close the shutter"
            mock_get_response.json.return_value = {
                "is_complete": False,
                "errors": [error_msg],
            }

            await eh2_shutter.set(ShutterDemand.CLOSE)

            mock_logger.error.assert_called_with(
                f"Plan operate_shutter_plan failed: {error_msg}"
            )
