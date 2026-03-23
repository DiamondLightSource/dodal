import pytest
from daq_config_server import ConfigClient

from dodal.beamlines import i03, i04


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
