from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_SOFT_UNDULATOR_LUT = join(TEST_DATA_PATH, "JIDEnergy2GapCalibrations.csv")
TEST_EXPECTED_UNDULATOR_LUT = join(TEST_DATA_PATH, "JIDEnergy2GapCalibrations.pkl")
__all__ = [
    "TEST_DATA_PATH",
    "TEST_SOFT_UNDULATOR_LUT",
]
