from unittest.mock import MagicMock, patch

from dodal.common.beamlines.config_client import get_config_client


@patch("dodal.common.beamlines.config_client.ConfigServer")
def test_by_default_get_config_client_uses_centrally_deployed_config_server(
    mock_config_server: MagicMock,
):
    get_config_client("")
    mock_config_server.assert_called_once_with(url="https://daq-config.diamond.ac.uk")


@patch("dodal.common.beamlines.config_client.ConfigServer")
def test_get_config_client_uses_i03_beamline_cluster_server_for_i03(
    mock_config_server: MagicMock,
):
    get_config_client("i03")
    mock_config_server.assert_called_once_with(
        url="https://i03-daq-config.diamond.ac.uk"
    )


@patch("dodal.common.beamlines.config_client.ConfigServer")
def test_get_config_client_uses_centrally_deployed_config_server_for_i04(
    mock_config_server: MagicMock,
):
    get_config_client("i04")
    mock_config_server.assert_called_once_with(url="https://daq-config.diamond.ac.uk")


@patch("dodal.common.beamlines.config_client.ConfigServer")
def test_get_config_client_caches_if_called_with_same_beamline(
    mock_config_server: MagicMock,
):
    get_config_client("i04")
    mock_config_server.assert_called_once()
    get_config_client("i04")
    mock_config_server.assert_called_once()


@patch("dodal.common.beamlines.config_client.ConfigServer")
def test_get_config_client_resets_cache_if_called_with_same_beamline(
    mock_config_server: MagicMock,
):
    assert mock_config_server.assert_not_called
    get_config_client("i04")
    mock_config_server.assert_called_once_with(url="https://daq-config.diamond.ac.uk")
    get_config_client("i03")
    assert mock_config_server.call_count == 2
    mock_config_server.assert_called_with(url="https://i03-daq-config.diamond.ac.uk")
