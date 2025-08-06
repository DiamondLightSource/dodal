from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
BAD_BEAMLINE_PARAMETERS = join(TEST_DATA_PATH, "bad_beamlineParameters")
I04_BEAMLINE_PARAMETERS = join(TEST_DATA_PATH, "i04_beamlineParameters")
TEST_BEAMLINE_PARAMETERS_TXT = join(TEST_DATA_PATH, "test_beamline_parameters.txt")
TEST_DISPLAY_CONFIG = join(TEST_DATA_PATH, "test_display.configuration")
TEST_OAV_ZOOM_LEVELS_XML = join(TEST_DATA_PATH, "test_oav_zoom_levels.xml")

__all__ = [
    "BAD_BEAMLINE_PARAMETERS",
    "I04_BEAMLINE_PARAMETERS",
    "TEST_BEAMLINE_PARAMETERS_TXT",
    "TEST_DISPLAY_CONFIG",
    "TEST_OAV_ZOOM_LEVELS_XML",
]
