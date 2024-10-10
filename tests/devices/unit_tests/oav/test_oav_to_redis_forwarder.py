import asyncio
import io
import pickle
from datetime import timedelta
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import DeviceCollector, set_mock_value
from PIL import Image

from dodal.devices.oav.oav_to_redis_forwarder import (
    OAVToRedisForwarder,
    Source,
    get_next_jpeg,
)


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis", new=AsyncMock)
def oav_forwarder(RE):
    with DeviceCollector(mock=True):
        oav_forwarder = OAVToRedisForwarder("prefix", "host", "password")
    set_mock_value(
        oav_forwarder._sources[Source.FULL_SCREEN.value], "test-full-screen-stream-url"
    )
    set_mock_value(oav_forwarder._sources[Source.ROI.value], "test-roi-stream-url")
    return oav_forwarder


@pytest.fixture
def oav_forwarder_with_valid_response(oav_forwarder):
    client_session_patch = patch(
        "dodal.devices.oav.oav_to_redis_forwarder.ClientSession.get", autospec=True
    )
    mock_get = client_session_patch.start()
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.content_type = "multipart/x-mixed-replace"
    oav_forwarder._get_frame_and_put_to_redis = AsyncMock()
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

    await oav_forwarder.kickoff()

    await asyncio.sleep(0.01)
    oav_forwarder._get_frame_and_put_to_redis.assert_called_once_with(mock_response)

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


def get_mock_response(jpeg_bytes):
    mock_response = MagicMock()
    mock_response.content.readline = AsyncMock(return_value=jpeg_bytes[:3])
    mock_response.content.readuntil = AsyncMock(return_value=jpeg_bytes[3:])
    return mock_response


async def test_given_byte_stream_when_get_next_jpeg_called_then_jpeg_bytes_returned():
    expected_bytes = b"\xff\xd8\x67\xce\xff\xd9"
    mock_response = get_mock_response(expected_bytes)
    bytes = await get_next_jpeg(mock_response)
    assert bytes == expected_bytes
    mock_response.content.readuntil.assert_awaited_once_with(b"\xff\xd9")


def _convert_numpy_data_into_jpeg_bytes(np_array):
    img = Image.fromarray(np_array)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="jpeg")
    img_byte_arr.seek(0)
    return img_byte_arr.read()


def _mock_response(numpy_image=None):
    if numpy_image is None:
        numpy_image = np.zeros((10, 10, 3), dtype=np.uint8)
    all_bytes = _convert_numpy_data_into_jpeg_bytes(numpy_image)
    return get_mock_response(all_bytes)


async def test_when_get_frame_and_put_to_redis_called_then_data_put_in_redis_under_sample_id(
    oav_forwarder,
):
    SAMPLE_ID = 100
    await oav_forwarder.sample_id.set(SAMPLE_ID)
    await oav_forwarder._get_frame_and_put_to_redis(_mock_response())
    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    assert redis_call[0] == str(SAMPLE_ID)


async def test_when_get_frame_and_put_to_redis_called_then_data_converted_to_image_and_sent_to_redis(
    oav_forwarder,
):
    expected_in_redis = np.zeros((10, 10, 3), dtype=np.uint8)
    await oav_forwarder._get_frame_and_put_to_redis(_mock_response(expected_in_redis))
    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    np.testing.assert_array_equal(pickle.loads(redis_call[2]), expected_in_redis)


async def test_when_get_frame_and_put_to_redis_called_then_data_put_in_redis_with_expiry_time(
    oav_forwarder,
):
    SAMPLE_ID = 100
    await oav_forwarder.sample_id.set(SAMPLE_ID)
    await oav_forwarder._get_frame_and_put_to_redis(_mock_response())
    redis_expire_call = oav_forwarder.redis_client.expire.call_args[0]
    assert redis_expire_call[0] == str(SAMPLE_ID)
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
    oav_forwarder.selected_source.set(source)

    await oav_forwarder.kickoff()
    await oav_forwarder.complete()

    mock_get.assert_called_with(ANY, expected_url)
