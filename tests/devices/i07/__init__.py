from os.path import join
from pathlib import Path

TEST_LOOKUP_TABLE_PATH = join(Path(__file__).parent, "IIDCalibrationTable.txt")
__all__ = [
    "TEST_LOOKUP_TABLE_PATH",
]
