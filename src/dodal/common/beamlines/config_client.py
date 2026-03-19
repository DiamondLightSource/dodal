from functools import cache

from daq_config_server import ConfigClient

BEAMLINE_CONFIG_SERVER_ENDPOINTS = {
    "i03": "https://i03-daq-config.diamond.ac.uk",
    "i04": "https://i04-daq-config.diamond.ac.uk",
}


@cache
def get_config_client(beamline: str) -> ConfigClient:
    print(beamline)
    print(BEAMLINE_CONFIG_SERVER_ENDPOINTS)
    url = BEAMLINE_CONFIG_SERVER_ENDPOINTS.get(
        beamline, "https://daq-config.diamond.ac.uk"
    )
    return ConfigClient(url=url)
