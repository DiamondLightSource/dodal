import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client_exceptions import ClientConnectorError
from ophyd_async.core import init_devices, set_mock_value
from tests.devices.oav.conftest import (
    oav_beam_centre_pv_fs,  # noqa: F401
    oav_beam_centre_pv_roi,  # noqa: F401
)

from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_to_redis_forwarder import OAVToRedisForwarder, Source


def _oav_to_redis_forwarder(
    mock,
    oav_roi: OAV,
    oav_fs: OAV,
):
    with init_devices(mock=mock):
        oav_forwarder = OAVToRedisForwarder(
            "BL04I-DI-OAV-01:",
            oav_roi,
            oav_fs,
            "",
            "",
        )
    oav_forwarder.redis_client.hset = AsyncMock()
    oav_forwarder.redis_client.expire = AsyncMock()
    return oav_forwarder


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis")
def oav_to_redis_forwarder(_, oav_beam_centre_pv_roi, oav_beam_centre_pv_fs):
    return _oav_to_redis_forwarder(False, oav_beam_centre_pv_roi, oav_beam_centre_pv_fs)


@pytest.fixture
@patch("dodal.devices.oav.oav_to_redis_forwarder.StrictRedis")
def mock_oav_to_redis_forwarder(_, oav_beam_centre_pv_roi, oav_beam_centre_pv_fs):
    return _oav_to_redis_forwarder(True, oav_beam_centre_pv_roi, oav_beam_centre_pv_fs)


def _set_url(mock_oav_to_redis_forwarder: OAVToRedisForwarder, url: str):
    set_mock_value(
        mock_oav_to_redis_forwarder.sources[Source.FULL_SCREEN.value].url_ref._obj,
        url,
    )
    set_mock_value(mock_oav_to_redis_forwarder.selected_source, Source.FULL_SCREEN)


@pytest.fixture
def static_http_server(tmp_path: Path):
    class HandlerInTestDirectory(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

    server_address = ("", 9876)
    httpd = HTTPServer(server_address, HandlerInTestDirectory)

    def run_server():
        httpd.serve_forever()
        httpd.server_close()

    server_thread = Thread(
        group=None, target=run_server, name="Test server", daemon=True
    )
    server_thread.start()
    try:
        yield
    finally:
        httpd.shutdown()
        server_thread.join()


async def test_given_stream_url_is_not_a_real_webpage_when_kickoff_then_error(
    mock_oav_to_redis_forwarder: OAVToRedisForwarder,
):
    _set_url(mock_oav_to_redis_forwarder, "http://localhost:9875/")
    with pytest.raises(ClientConnectorError):
        await mock_oav_to_redis_forwarder.kickoff()


async def test_given_stream_url_is_real_webpage_but_not_mjpg_when_kickoff_then_error(
    mock_oav_to_redis_forwarder: OAVToRedisForwarder, static_http_server
):
    url = "http://localhost:9876/"
    _set_url(mock_oav_to_redis_forwarder, url)
    with pytest.raises(ValueError) as e:
        await mock_oav_to_redis_forwarder.kickoff()
    assert url in str(e.value)


@pytest.mark.requires(instrument="i04")  # connects to the real beamline. See
# https://github.com/DiamondLightSource/mx-bluesky/issues/183
async def test_given_valid_stream_when_kickoff_then_multiple_images_written_to_redis(
    oav_to_redis_forwarder: OAVToRedisForwarder,
):
    await oav_to_redis_forwarder.kickoff()
    await asyncio.sleep(0.5)
    await oav_to_redis_forwarder.complete()
    assert oav_to_redis_forwarder.redis_client.hset.call_count > 1  # type:ignore
