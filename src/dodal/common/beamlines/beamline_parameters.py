from typing import Any

from dodal.common.beamlines.config_client import get_config_client

BEAMLINE_PARAMETER_PATHS = {
    "i03": "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters",
    "i04": "/dls_sw/i04/software/daq_configuration/domain/beamlineParameters",
}


def get_beamline_parameters(
    beamline: str, beamline_param_path: str | None = None
) -> dict[str, Any]:
    """Loads the beamline parameters from the specified path, or according to the
    environment variable if none is given"""
    if not beamline_param_path:
        beamline_param_path = BEAMLINE_PARAMETER_PATHS.get(beamline)
        if beamline_param_path is None:
            raise KeyError(
                "No beamline parameter path found, maybe 'BEAMLINE' environment variable is not set!"
            )
    config_client = get_config_client(beamline)
    return config_client.get_file_contents(
        beamline_param_path, dict, reset_cached_result=True
    )
