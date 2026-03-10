from functools import cache

from daq_config_server.app.client import ConfigClient

BEAMLINE_CONFIG_SERVER_ENDPOINTS = {
    "i03": "https://i03-daq-config.diamond.ac.uk",
    "i04": "https://daq-config.diamond.ac.uk",
}


@cache
def get_config_client(beamline: str) -> ConfigClient:
    url = BEAMLINE_CONFIG_SERVER_ENDPOINTS.get(
        beamline, "https://daq-config.diamond.ac.uk"
    )
    return ConfigClient(url=url)
