import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client_exceptions import ClientConnectorError
from ophyd_async.core import DeviceCollector

from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis")
def oav_to_redis_forwarder(_, RE):
    with DeviceCollector():
        oav_forwarder = OAVToRedisForwarder("BL04I", "", "")
    oav_forwarder.redis_client.hset = AsyncMock()
    return oav_forwarder


@pytest.mark.s03  # Doesn't actually depend on s03, just on DLS network. See https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_stream_url_is_not_a_real_webpage_when_kickoff_then_error(
    oav_to_redis_forwarder: OAVToRedisForwarder,
):
    oav_to_redis_forwarder.stream_url = AsyncMock()
    oav_to_redis_forwarder.stream_url.get_value.return_value = (
        "http://www.this_is_not_a_valid_webpage.com/"
    )
    with pytest.raises(ClientConnectorError):
        await oav_to_redis_forwarder.kickoff()


@pytest.mark.s03  # Doesn't actually depend on s03, just on DLS network. See https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_stream_url_is_real_webpage_but_not_mjpg_when_kickoff_then_error(
    oav_to_redis_forwarder: OAVToRedisForwarder,
):
    URL = "https://www.google.com/"
    oav_to_redis_forwarder.stream_url = AsyncMock()
    oav_to_redis_forwarder.stream_url.get_value.return_value = URL
    with pytest.raises(ValueError) as e:
        await oav_to_redis_forwarder.kickoff()
    assert URL in str(e.value)


@pytest.mark.s03  # Doesn't actually depend on s03, just on DLS network. See https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_valid_stream_when_kickoff_then_multiple_images_written_to_redis(
    oav_to_redis_forwarder: OAVToRedisForwarder,
):
    await oav_to_redis_forwarder.kickoff()
    await asyncio.sleep(0.5)
    await oav_to_redis_forwarder.complete()
    assert oav_to_redis_forwarder.redis_client.hset.call_count > 1  # type:ignore
