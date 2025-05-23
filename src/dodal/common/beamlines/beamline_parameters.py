import ast
from typing import Any, cast

from dodal.log import LOGGER
from dodal.utils import get_beamline_name

BEAMLINE_PARAMETER_KEYWORDS = ["FB", "FULL", "deadtime"]

BEAMLINE_PARAMETER_PATHS = {
    "i03": "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters",
    "i04": "/dls_sw/i04/software/gda_versions/gda_9_34/workspace_git/gda-mx.git/configurations/i04-config/scripts/beamlineParameters",
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
    def from_lines(cls, file_name: str, config_lines: list[str]):
        config_lines_nocomments = [line.split("#", 1)[0] for line in config_lines]
        config_lines_sep_key_and_value = [
            # XXX removes all whitespace instead of just trim
            line.translate(str.maketrans("", "", " \n\t\r")).split("=")
            for line in config_lines_nocomments
        ]
        config_pairs: list[tuple[str, Any]] = [
            cast(tuple[str, Any], param)
            for param in config_lines_sep_key_and_value
            if len(param) == 2
        ]
        for i, (param, value) in enumerate(config_pairs):
            try:
                # BEAMLINE_PARAMETER_KEYWORDS effectively raw string but whitespace removed
                if value not in BEAMLINE_PARAMETER_KEYWORDS:
                    config_pairs[i] = (
                        param,
                        cls.parse_value(value),
                    )
            except Exception as e:
                LOGGER.warning(f"Unable to parse {file_name} line {i}: {e}")

        return cls(params=dict(config_pairs))

    @classmethod
    def from_file(cls, path: str):
        with open(path) as f:
            config_lines = f.readlines()
        return cls.from_lines(path, config_lines)

    @classmethod
    def parse_value(cls, value: str):
        return ast.literal_eval(value.replace("Yes", "True").replace("No", "False"))


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
