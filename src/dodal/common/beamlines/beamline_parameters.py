from typing import Any

from dodal.common.beamlines.config_client import get_config_client

BEAMLINE_PARAMETER_PATHS = {
    "i03": "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters",
    "i04": "/dls_sw/i04/software/daq_configuration/domain/beamlineParameters",
}


def get_beamline_parameters(beamline: str) -> dict[str, Any]:
    """Loads the beamline parameters for a specified beamline from the config server.

    Args:
        beamline (str): The beamline for which beamline parameters will be retrieved.

    Returns:
        dict[str, Any]: Dict of beamline parameters.
    """
    beamline_param_path = BEAMLINE_PARAMETER_PATHS.get(beamline)
    if beamline_param_path is None:
        raise KeyError(
            "No beamline parameter path found, maybe 'BEAMLINE' environment variable is not set!"
        )
    config_client = get_config_client(beamline)
    return config_client.get_file_contents(beamline_param_path, dict)
