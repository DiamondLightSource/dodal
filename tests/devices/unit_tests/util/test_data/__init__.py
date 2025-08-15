from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_BEAMLINE_DCM_ROLL_CONVERTER_NON_MONOTONIC_TXT = join(
    TEST_DATA_PATH, "test_beamline_dcm_roll_converter_non_monotonic.txt"
)
TEST_BEAMLINE_DCM_ROLL_CONVERTER_REVERESED_TXT = join(
    TEST_DATA_PATH, "test_beamline_dcm_roll_converter_reversed.txt"
)
TEST_BEAMLINE_DCM_ROLL_CONVERTER_TXT = join(
    TEST_DATA_PATH, "test_beamline_dcm_roll_converter.txt"
)

__all__ = [
    "TEST_BEAMLINE_DCM_ROLL_CONVERTER_NON_MONOTONIC_TXT",
    "TEST_BEAMLINE_DCM_ROLL_CONVERTER_REVERESED_TXT",
    "TEST_BEAMLINE_DCM_ROLL_CONVERTER_TXT",
]
