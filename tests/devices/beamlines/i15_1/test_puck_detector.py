from collections.abc import AsyncGenerator
from json import JSONDecodeError
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client import ClientSession, InvalidUrlClientError
from aiohttp.test_utils import TestClient, TestServer, unused_port
from aiohttp.web import Response
from aiohttp.web_app import Application
from ophyd_async.core import init_devices

from dodal.devices.beamlines.i15_1.puck_detector import PuckDetect, PuckState

full_test_json = """{
  "result": {
    "1": "Puck",
    "2": "Lid",
    "3": "None",
    "4": "None",
    "5": "None",
    "6": "None",
    "7": "None",
    "8": "None",
    "9": "None",
    "10": "None",
    "11": "Lid",
    "12": "None",
    "13": "Puck",
    "14": "Puck",
    "15": "None",
    "16": "None",
    "17": "None",
    "18": "None",
    "19": "None",
    "20": "None"
  }
}
"""


@pytest.fixture
def data_coro(request) -> AsyncMock:
    body = getattr(request, "param", "{}")
    return AsyncMock(return_value=Response(body=body))


@pytest.fixture
def server_port() -> int:
    return unused_port()


@pytest.fixture
async def test_client(
    data_coro: AsyncMock, server_port: int
) -> AsyncGenerator[TestClient]:
    app = Application()
    app.router.add_get("/result", handler=data_coro)
    client = TestClient(server=TestServer(app, port=server_port))
    await client.start_server()
    yield client
    await client.close()


@pytest.fixture
async def puck_detect(
    test_client: TestClient,
    server_port: int,
) -> AsyncGenerator[PuckDetect]:
    url = f"http://127.0.0.1:{server_port}/result"

    def get_session(raise_for_status: bool) -> ClientSession:
        return test_client.session

    with patch(
        "dodal.devices.beamlines.i15_1.puck_detector.ClientSession", new=get_session
    ):
        async with init_devices(mock=True):
            puck_detect = PuckDetect(url, 1)
        yield puck_detect


async def test_given_web_page_not_accessible_when_triggered_then_error_raised():
    async with init_devices(mock=True):
        puck_detect = PuckDetect("bad_url")

    with pytest.raises(InvalidUrlClientError):
        await puck_detect.trigger()


@pytest.mark.parametrize("data_coro", ["{1}"], indirect=True)
async def test_given_malformed_json_when_triggered_then_error_raised(
    puck_detect: PuckDetect,
):
    with pytest.raises(JSONDecodeError):
        await puck_detect.trigger()


@pytest.mark.parametrize("data_coro", ['{"result": {"1": "None"}}'], indirect=True)
async def test_given_nothing_found_at_position_1_when_triggered_then_position_1_set_to_nothing(
    puck_detect: PuckDetect,
):
    await puck_detect.trigger()
    assert await puck_detect.puck_states[1].get_value() == PuckState.NO_PUCK


@pytest.mark.parametrize("data_coro", ['{"result": {"1": "Puck"}}'], indirect=True)
async def test_given_puck_found_at_position_1_when_triggered_then_position_1_set_to_puck(
    puck_detect: PuckDetect,
):
    await puck_detect.trigger()
    assert await puck_detect.puck_states[1].get_value() == PuckState.PUCK


@pytest.mark.parametrize("data_coro", ['{"result": {"1": "Lid"}}'], indirect=True)
async def test_given_lid_found_at_position_1_when_triggered_then_position_1_set_to_lid(
    puck_detect: PuckDetect,
):
    await puck_detect.trigger()
    assert await puck_detect.puck_states[1].get_value() == PuckState.LID


@pytest.mark.parametrize("data_coro", ['{"result": {"1": "Unknown"}}'], indirect=True)
async def test_given_unexpected_state_found_at_position_1_when_triggered_then_sensible_error(
    puck_detect: PuckDetect,
):
    with pytest.raises(ValueError):
        await puck_detect.trigger()


@pytest.mark.parametrize(
    "data_coro", ['{"result": {"1": "Lid", "2": "None"}}'], indirect=True
)
async def test_given_more_states_than_expected_when_triggered_then_sensible_error(
    puck_detect: PuckDetect,
):
    with pytest.raises(ValueError):
        await puck_detect.trigger()


@pytest.mark.parametrize("data_coro", [full_test_json], indirect=True)
async def test_given_full_test_json_when_triggered_then_positions_set_as_expected(
    test_client: TestClient,
    server_port: int,
):
    url = f"http://127.0.0.1:{server_port}/result"

    def get_session(raise_for_status: bool) -> ClientSession:
        return test_client.session

    with patch(
        "dodal.devices.beamlines.i15_1.puck_detector.ClientSession", new=get_session
    ):
        async with init_devices(mock=True):
            puck_detect = PuckDetect(url, 20)

    await puck_detect.trigger()
    assert await puck_detect.puck_states[1].get_value() == PuckState.PUCK
    assert await puck_detect.puck_states[2].get_value() == PuckState.LID
    assert await puck_detect.puck_states[3].get_value() == PuckState.NO_PUCK
    assert await puck_detect.puck_states[10].get_value() == PuckState.NO_PUCK
    assert await puck_detect.puck_states[14].get_value() == PuckState.PUCK
