from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_OAV_CENTRING_JSON = join(TEST_DATA_PATH, "test_OAVCentring.json")
OAV_SNAPSHOT_TEST_PNG = join(TEST_DATA_PATH, "oav_snapshot_test.png")
OAV_SNAPSHOT_EXPECTED_PNG = join(TEST_DATA_PATH, "oav_snapshot_expected.png")

__all__ = [
    "OAV_SNAPSHOT_EXPECTED_PNG",
    "OAV_SNAPSHOT_TEST_PNG",
    "TEST_OAV_CENTRING_JSON",
]
