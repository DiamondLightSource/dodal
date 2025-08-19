from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT = join(
    TEST_DATA_PATH, "test_beamline_undulator_to_gap_lookup_table.txt"
)
TEST_LUT_TXT = join(TEST_DATA_PATH, "test_lookup_table.txt")
__all__ = [
    "TEST_BEAMLINE_UNDULATOR_TO_GAP_LUT",
    "TEST_DATA_PATH",
    "TEST_LUT_TXT",
]
