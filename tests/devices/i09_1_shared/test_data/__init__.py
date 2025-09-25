from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_HARD_UNDULATOR_LUT = join(TEST_DATA_PATH, "test_hard_undulator_lookup_table.txt")
__all__ = ["TEST_DATA_PATH", "TEST_HARD_UNDULATOR_LUT"]
