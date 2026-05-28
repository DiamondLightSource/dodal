from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
TEST_VGSCIENTA_SEQUENCE = join(TEST_DATA_PATH, "vgscienta_sequence.seq")
TEST_SPECS_SEQUENCE = join(TEST_DATA_PATH, "specs_sequence.seq")
TEST_MBS_XML_SEQUENCE = join(TEST_DATA_PATH, "mbs_region1.arpes")

__all__ = ["TEST_SPECS_SEQUENCE", "TEST_VGSCIENTA_SEQUENCE", "TEST_MBS_XML_SEQUENCE"]
