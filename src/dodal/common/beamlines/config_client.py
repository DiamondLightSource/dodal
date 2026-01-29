from daq_config_server.client import ConfigServer

BEAMLINE_CONFIG_SERVER_ENDPOINTS = {
    "i03": "https://i03-daq-config.diamond.ac.uk",
    "i04": "https://daq-config.diamond.ac.uk",
}


def get_config_client(beamline: str) -> ConfigServer:
    url = BEAMLINE_CONFIG_SERVER_ENDPOINTS.get(
        beamline, "https://daq-config.diamond.ac.uk"
    )
    return ConfigServer(url=url)
