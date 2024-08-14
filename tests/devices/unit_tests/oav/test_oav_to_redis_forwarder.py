import asyncio
import io
import pickle
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import DeviceCollector, set_mock_value
from PIL import Image

from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder, get_next_jpeg


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis", new=AsyncMock)
def oav_forwarder(RE):
    with DeviceCollector(mock=True):
        oav_forwarder = OAVToRedisForwarder("prefix", "host", "password")
    set_mock_value(oav_forwarder.stream_url, "test-stream-url")
    return oav_forwarder


@patch("dodal.devices.oav.oav_to_redis_forwarder.ClientSession.get", autospec=True)
async def test_when_oav_forwarder_kicked_off_then_connection_open_and_data_streamed(
    mock_get, oav_forwarder
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())

    oav_forwarder._get_frame_and_put_to_redis = AsyncMock()

    await oav_forwarder.kickoff()

    await asyncio.sleep(0.01)
    oav_forwarder._get_frame_and_put_to_redis.assert_called_once_with(mock_response)

    await oav_forwarder.complete()


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


async def test_when_get_frame_and_put_to_redis_called_then_data_converted_to_image_and_sent_to_redis(
    oav_forwarder,
):
    expected_in_redis = np.zeros((10, 10, 3), dtype=np.uint8)
    all_bytes = _convert_numpy_data_into_jpeg_bytes(expected_in_redis)
    mock_response = get_mock_response(all_bytes)
    await oav_forwarder._get_frame_and_put_to_redis(mock_response)
    redis_call = oav_forwarder.redis_client.hset.call_args[0]
    assert redis_call[0] == "test-image"
    np.testing.assert_array_equal(pickle.loads(redis_call[2]), expected_in_redis)
