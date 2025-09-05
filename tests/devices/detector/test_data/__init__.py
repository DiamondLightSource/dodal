from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_DET_DIST_CONVERTER_LUT = join(TEST_DATA_PATH, "test_det_dist_converter.txt")

__all__ = ["TEST_DET_DIST_CONVERTER_LUT"]
