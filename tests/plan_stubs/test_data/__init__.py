from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_TOPUP_SHORT_PARAMS_TXT = join(TEST_DATA_PATH, "topup_short_params.txt")
TEST_TOPUP_LONG_DELAY_TXT = join(TEST_DATA_PATH, "topup_long_delay.txt")

__all__ = [
    "TEST_TOPUP_SHORT_PARAMS_TXT",
    "TEST_TOPUP_LONG_DELAY_TXT",
]
