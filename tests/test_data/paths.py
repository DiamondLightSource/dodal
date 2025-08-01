from os.path import join
from pathlib import Path

TEST_DATA_PATH = Path(__file__).parent
BAD_BEAMLINE_PARAMETERS = join(TEST_DATA_PATH, "bad_beamlineParameters")
I04_BEAMLINE_PARAMETERS = join(TEST_DATA_PATH, "i04_beamlineParameters")
TEST_BEAMLINE_PARAMETERS_TXT = join(TEST_DATA_PATH, "test_beamline_parameters.txt")
TEST_DISPLAY_CONFIG = join(TEST_DATA_PATH, "test_display.configuration")
TEST_J_CAMERA_MAN_ZOOM_LEVELS_XML = join(
    TEST_DATA_PATH, "test_jCameraManZoomLevels.xml"
)
