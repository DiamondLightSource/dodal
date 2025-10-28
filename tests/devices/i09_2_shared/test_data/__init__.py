from os import fspath
from os.path import join
from pathlib import Path

LOOKUP_TABLE_PATH = fspath(Path(__file__).parent)
TEST_SOFT_UNDULATOR_LUT = join(LOOKUP_TABLE_PATH, "JIDEnergy2GapCalibrations.csv")
TEST_EXPECTED_UNDULATOR_LUT = join(LOOKUP_TABLE_PATH, "JIDEnergy2GapCalibrations.pkl")
__all__ = [
    "LOOKUP_TABLE_PATH",
    "TEST_SOFT_UNDULATOR_LUT",
    "TEST_EXPECTED_UNDULATOR_LUT",
]
