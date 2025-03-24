from unittest.mock import ANY, AsyncMock, patch

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


@pytest.fixture
async def test_shutter(RE: RunEngine) -> AccessControlledShutter:
    shutter = AccessControlledShutter("", HutchState.EH2, name="mock_shutter")
    await shutter.connect(mock=True)

    shutter.url = "http://test-blueapi.url"
    set_mock_value(shutter.shutter_status, ShutterState.CLOSED)
    return shutter


async def test_read_on_shutter_device_returns_correct_status(
    test_shutter: AccessControlledShutter,
):
    reading = await test_shutter.read()
    assert reading == {
        "shutter_status": {
            "timestamp": ANY,
            "value": "Closed",
        }
    }


async def test_set_raises_error_if_post_not_successful(test_shutter):
    with pytest.raises(ClientConnectionError):
        with patch("dodal.devices.i19.shutter.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = (
                mock_response := AsyncMock()
            )
            mock_response.ok = False

            await test_shutter.set(ShutterDemand.OPEN)


async def test_set_corrently_makes_rest_calls(test_shutter):
    test_request = {
        "name": "operate_shutter_plan",
        "params": {"from_hutch": "EH2", "shutter_demand": ShutterDemand.OPEN},
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

        await test_shutter.set(ShutterDemand.OPEN)

        mock_post.assert_called_with("/tasks", data=test_request)
        mock_put.assert_called_with("/worker/tasks", data={"task_id": 1})
