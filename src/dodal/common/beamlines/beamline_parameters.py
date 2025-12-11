from typing import Any

from daq_config_server.client import ConfigServer

from dodal.utils import get_beamline_name

BEAMLINE_PARAMETER_KEYWORDS = ["FB", "FULL", "deadtime"]

BEAMLINE_PARAMETER_PATHS = {
    "i03": "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters",
    "i04": "/dls_sw/i04/software/daq_configuration/domain/beamlineParameters",
}


class GDABeamlineParameters:
    params: dict[str, Any]

    def __init__(self, params: dict[str, Any]):
        self.params = params

    def __repr__(self) -> str:
        return repr(self.params)

    def __getitem__(self, item: str):
        return self.params[item]

    @classmethod
    def from_file(cls, path: str):
        config_server = ConfigServer(url="https://daq-config.diamond.ac.uk")
        return cls(
            params=config_server.get_file_contents(path, dict, reset_cached_result=True)
        )


def get_beamline_parameters(beamline_param_path: str | None = None):
    """Loads the beamline parameters from the specified path, or according to the
    environment variable if none is given"""
    if not beamline_param_path:
        beamline_name = get_beamline_name("i03")
        beamline_param_path = BEAMLINE_PARAMETER_PATHS.get(beamline_name)
        if beamline_param_path is None:
            raise KeyError(
                "No beamline parameter path found, maybe 'BEAMLINE' environment variable is not set!"
            )
    return GDABeamlineParameters.from_file(beamline_param_path)
