from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from aiohttp.client import ClientConnectionError
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.hutch_shutter import (
    ShutterDemand,
    ShutterState,
)
from dodal.devices.i19.shutter import (
    AccessControlledShutter,
    HutchState,
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
        with patch("dodal.devices.i19.shutter.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = (
                mock_response := AsyncMock()
            )
            mock_response.ok = False

            await eh2_shutter.set(ShutterDemand.OPEN)


@patch("dodal.devices.i19.shutter.LOGGER")
async def test_no_task_id_returned_from_post(
    mock_logger: MagicMock, eh1_shutter: AccessControlledShutter
):
    with pytest.raises(KeyError):
        with (
            patch("dodal.devices.i19.shutter.ClientSession.post") as mock_post,
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
            "shutter_demand": shutter_demand,
        },
    }
    with (
        patch("dodal.devices.i19.shutter.ClientSession.post") as mock_post,
        patch("dodal.devices.i19.shutter.ClientSession.put") as mock_put,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": 1}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = True

        await eh2_shutter.set(shutter_demand)

        mock_post.assert_called_with("/tasks", data=test_request)
        mock_put.assert_called_with("/worker/tasks", data={"task_id": 1})


@patch("dodal.devices.i19.shutter.LOGGER")
async def test_if_put_fails_log_a_warning_and_return(
    mock_logger: MagicMock, eh1_shutter: AccessControlledShutter
):
    with (
        patch("dodal.devices.i19.shutter.ClientSession.post") as mock_post,
        patch("dodal.devices.i19.shutter.ClientSession.put") as mock_put,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": 1}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = False

        await eh1_shutter.set(ShutterDemand.OPEN)

        mock_logger.warning.assert_called_once()
