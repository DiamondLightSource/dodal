from os.path import join
from pathlib import Path

LOOKUP_PATH = Path(__file__).parent

BEAMLINE_ENERGY_DCM_PITCH_CONVERTER_TXT = join(
    LOOKUP_PATH, "BeamLineEnergy_DCM_Pitch_converter.txt"
)
BEAMLINE_ENERGY_DCM_ROLL_CONVERTER_TXT = join(
    LOOKUP_PATH, "BeamLineEnergy_DCM_Roll_converter.txt"
)

__all__ = [
    "LOOKUP_PATH",
    "BEAMLINE_ENERGY_DCM_PITCH_CONVERTER_TXT",
    "BEAMLINE_ENERGY_DCM_ROLL_CONVERTER_TXT",
]
