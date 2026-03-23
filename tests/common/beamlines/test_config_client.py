from unittest.mock import MagicMock, patch

import pytest
from daq_config_server import ConfigClient

from dodal.beamlines import i03, i04
from dodal.common.beamlines.beamline_utils import get_config_client


@pytest.mark.parametrize(
    "client, expected_url",
    [
        (i03.config_client(), "https://i03-daq-config.diamond.ac.uk"),
        (i04.config_client(), "https://i04-daq-config.diamond.ac.uk"),
    ],
)
def test_config_client_has_correct_url_for_each_beamline(
    client: ConfigClient, expected_url: str
):
    assert client._url == expected_url


@patch("dodal.common.beamlines.config_client.ConfigClient")
def test_get_config_client_caches_if_called_with_same_beamline(
    mock_config_client: MagicMock,
):
    get_config_client()
    mock_config_client.assert_called_once()
    get_config_client()
    mock_config_client.assert_called_once()


@patch("dodal.common.beamlines.config_client.ConfigClient")
def test_get_config_client_resets_cache_if_called_with_same_beamline(
    mock_config_client: MagicMock,
):
    assert mock_config_client.assert_not_called
    get_config_client()
    mock_config_client.assert_called_once_with(
        url="https://i04-daq-config.diamond.ac.uk"
    )
    get_config_client()
    assert mock_config_client.call_count == 2
    mock_config_client.assert_called_with(url="https://i03-daq-config.diamond.ac.uk")
