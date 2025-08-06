from os.path import join
from pathlib import Path

DOMAIN_PATH = Path(__file__).parent
BEAMLINE_PARAMETERS = join(DOMAIN_PATH, "beamlineParameters")

__all__ = [
    "DOMAIN_PATH",
    "BEAMLINE_PARAMETERS",
]
