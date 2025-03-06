import asyncio
from datetime import timedelta
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_to_redis_forwarder import (
    OAVToRedisForwarder,
    Source,
    get_next_jpeg,
)


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis", new=AsyncMock)
async def oav_forwarder(RE):
    with init_devices(mock=True):
        oav_forwarder = OAVToRedisForwarder("prefix", "host", "password")
    set_mock_value(
        oav_forwarder.sources[Source.FULL_SCREEN.value].url,
        "test-full-screen-stream-url",
    )
    set_mock_value(oav_forwarder.sources[Source.ROI.value].url, "test-roi-stream-url")
    set_mock_value(oav_forwarder.selected_source, Source.FULL_SCREEN.value)
    return oav_forwarder


def get_mock_response(jpeg_bytes: bytes | None = None):
    if not jpeg_bytes:
        jpeg_bytes = b"\xff\xd8\x67\xce\xff\xd9"
    mock_response = MagicMock()
    mock_response.content.readline = AsyncMock(return_value=jpeg_bytes[:3])
    mock_response.content.readuntil = AsyncMock(return_value=jpeg_bytes[3:])
    return mock_response


@pytest.fixture
def oav_forwarder_with_valid_response(oav_forwarder: OAVToRedisForwarder):
    client_session_patch = patch(
        "dodal.devices.oav.oav_to_redis_forwarder.ClientSession.get", autospec=True
    )
    mock_get = client_session_patch.start()
    mock_get.return_value.__aenter__.return_value = (
        mock_response := get_mock_response()
    )
    mock_response.content_type = "multipart/x-mixed-replace"
    yield oav_forwarder, mock_response, mock_get
    client_session_patch.stop()


@patch("dodal.devices.oav.oav_to_redis_forwarder.ClientSession.get", autospec=True)
async def test_given_response_is_not_mjpeg_when_oav_forwarder_kicked_off_then_exception_raised(
    mock_get, oav_forwarder
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.content_type = "bad_content_type"

    oav_forwarder._get_frame_and_put_to_redis = AsyncMock()

    with pytest.raises(ValueError):
        await oav_forwarder.kickoff()


async def test_when_oav_forwarder_kicked_off_then_connection_open_and_data_streamed(
    oav_forwarder_with_valid_response,
):
    oav_forwarder, mock_response, _ = oav_forwarder_with_valid_response
    oav_forwarder._get_frame_and_put_to_redis = AsyncMock()

    await oav_forwarder.kickoff()
    await asyncio.sleep(0.01)

    call_args = oav_forwarder._get_frame_and_put_to_redis.call_args

    assert call_args[0][0].startswith("fullscreen-0")
    assert call_args[0][1] == mock_response

    await oav_forwarder.complete()


async def test_when_oav_forwarder_kicked_off_then_stopped_forwarding_is_stopped(
    oav_forwarder_with_valid_response,
):
    oav_forwarder, _, _ = oav_forwarder_with_valid_response

    await oav_forwarder.kickoff()
    await oav_forwarder.stop()
    assert oav_forwarder.forwarding_task.done()


async def test_when_oav_forwarder_kicked_off_then_completed_forwarding_is_stopped(
    oav_forwarder_with_valid_response,
):
    oav_forwarder, _, _ = oav_forwarder_with_valid_response

    await oav_forwarder.kickoff()
    await oav_forwarder.complete()
    assert oav_forwarder.forwarding_task.done()


async def test_given_byte_stream_when_get_next_jpeg_called_then_jpeg_bytes_returned():
    expected_bytes = b"\xff\xd8\x67\xce\xff\xd9"
    mock_response = get_mock_response(expected_bytes)
    bytes = await get_next_jpeg(mock_response)
    assert bytes == expected_bytes
    mock_response.content.readuntil.assert_awaited_once_with(b"\xff\xd9")


async def test_when_get_frame_and_put_to_redis_called_then_data_put_in_redis_under_sample_id(
    oav_forwarder,
):
    SAMPLE_ID = 100
    await oav_forwarder.sample_id.set(SAMPLE_ID)
    await oav_forwarder._get_frame_and_put_to_redis(ANY, get_mock_response())
    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    assert redis_call[0] == "murko:100:raw"


async def test_when_get_frame_and_put_to_redis_called_then_data_is_jpeg_bytes(
    oav_forwarder,
):
    expected_bytes = b"\xff\xd8\x67\xce\xff\xd9"
    await oav_forwarder._get_frame_and_put_to_redis(
        ANY, get_mock_response(expected_bytes)
    )
    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    assert redis_call[2] == expected_bytes


async def test_when_get_frame_and_put_to_redis_called_then_data_put_in_redis_with_expiry_time(
    oav_forwarder,
):
    SAMPLE_ID = 100
    await oav_forwarder.sample_id.set(SAMPLE_ID)
    await oav_forwarder._get_frame_and_put_to_redis(ANY, get_mock_response())
    redis_expire_call = oav_forwarder.redis_client.expire.call_args[0]
    assert redis_expire_call[0] == "murko:100:raw"
    assert redis_expire_call[1] == timedelta(days=oav_forwarder.DATA_EXPIRY_DAYS)


@pytest.mark.parametrize(
    "source, expected_url",
    [
        (Source.FULL_SCREEN, "test-full-screen-stream-url"),
        (Source.ROI, "test-roi-stream-url"),
    ],
)
async def test_when_different_sources_selected_then_different_urls_used(
    oav_forwarder_with_valid_response, source, expected_url
):
    oav_forwarder, _, mock_get = oav_forwarder_with_valid_response
    set_mock_value(oav_forwarder.selected_source, source.value)

    await oav_forwarder.kickoff()
    await oav_forwarder.complete()

    mock_get.assert_called_with(ANY, expected_url)


@pytest.mark.parametrize(
    "source, expected_uuid_prefix",
    [
        (Source.FULL_SCREEN, "fullscreen"),
        (Source.ROI, "roi"),
    ],
)
async def test_when_different_sources_selected_then_different_uuids_used(
    oav_forwarder_with_valid_response, source, expected_uuid_prefix
):
    oav_forwarder, _, _ = oav_forwarder_with_valid_response
    set_mock_value(oav_forwarder.selected_source, source.value)

    await oav_forwarder.kickoff()
    await asyncio.sleep(0.01)
    await oav_forwarder.complete()

    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    assert redis_call[1].startswith(f"{expected_uuid_prefix}-0")


@pytest.mark.parametrize(
    "source, expected_uuid_prefix",
    [
        (Source.FULL_SCREEN, "fullscreen"),
        (Source.ROI, "roi"),
    ],
)
async def test_oav_only_forwards_data_when_the_unique_id_updates(
    oav_forwarder_with_valid_response, source, expected_uuid_prefix
):
    oav_forwarder, _, _ = oav_forwarder_with_valid_response
    set_mock_value(oav_forwarder.selected_source, source.value)
    await oav_forwarder.kickoff()
    await asyncio.sleep(0.01)
    oav_forwarder.redis_client.hset.assert_called_once()
    set_mock_value(oav_forwarder.counter, 1)
    await asyncio.sleep(0.01)
    assert oav_forwarder.redis_client.hset.call_count == 2
    second_call = oav_forwarder.redis_client.hset.call_args_list[1][0]
    assert second_call[1].startswith(f"{expected_uuid_prefix}-1")
    await oav_forwarder.complete()
