import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client_exceptions import ClientConnectorError
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder, Source


def _oav_to_redis_forwarder(mock):
    with init_devices(mock=mock):
        oav_forwarder = OAVToRedisForwarder("BL04I-DI-OAV-01:", "", "")
    oav_forwarder.redis_client.hset = AsyncMock()
    oav_forwarder.redis_client.expire = AsyncMock()
    return oav_forwarder


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis")
def oav_to_redis_forwarder(_, RE):
    return _oav_to_redis_forwarder(False)


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis")
def mock_oav_to_redis_forwarder(_, RE):
    return _oav_to_redis_forwarder(True)


def _set_url(mock_oav_to_redis_forwarder: OAVToRedisForwarder, url: str):
    set_mock_value(
        mock_oav_to_redis_forwarder.sources[Source.FULL_SCREEN.value].url,
        url,
    )
    set_mock_value(mock_oav_to_redis_forwarder.selected_source, Source.FULL_SCREEN)


@pytest.mark.system_test  # depends on external webpage. See
# https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_stream_url_is_not_a_real_webpage_when_kickoff_then_error(
    mock_oav_to_redis_forwarder: OAVToRedisForwarder,
):
    _set_url(mock_oav_to_redis_forwarder, "http://www.this_is_not_a_valid_webpage.com/")
    with pytest.raises(ClientConnectorError):
        await mock_oav_to_redis_forwarder.kickoff()


@pytest.mark.system_test  # depends on external webpage.
# See https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_stream_url_is_real_webpage_but_not_mjpg_when_kickoff_then_error(
    mock_oav_to_redis_forwarder: OAVToRedisForwarder,
):
    URL = "https://www.google.com/"
    _set_url(mock_oav_to_redis_forwarder, URL)
    with pytest.raises(ValueError) as e:
        await mock_oav_to_redis_forwarder.kickoff()
    assert URL in str(e.value)


@pytest.mark.system_test  # connects to the real beamline. See
# https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_valid_stream_when_kickoff_then_multiple_images_written_to_redis(
    oav_to_redis_forwarder: OAVToRedisForwarder,
):
    await oav_to_redis_forwarder.kickoff()
    await asyncio.sleep(0.5)
    await oav_to_redis_forwarder.complete()
    assert oav_to_redis_forwarder.redis_client.hset.call_count > 1  # type:ignore
