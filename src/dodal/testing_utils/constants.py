from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE

MOCK_DAQ_CONFIG_PATH = "tests/devices/unit_tests/test_daq_configuration"
ID_GAP_LOOKUP_TABLE_PATH: str = (
    "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
)
MOCK_PATHS = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"),
    ("DISPLAY_CONFIG", "tests/devices/unit_tests/test_display.configuration"),
]
MOCK_ATTRIBUTES_TABLE = {
    "i03": MOCK_PATHS,
    "s03": MOCK_PATHS,
    "i04": MOCK_PATHS,
    "s04": MOCK_PATHS,
}
EIGER_DETECTOR_SIZE_CONSTANTS = EIGER2_X_16M_SIZE
EIGER_EXPECTED_ENERGY = 100.0
EIGER_EXPOSURE_TIME = 1.0
EIGER_DIR = "/test/dir"
EIGER_PREFIX = "test"
EIGER_RUN_NUMBER = 0
EIGER_DETECTOR_DISTANCE = 1.0
EIGER_OMEGA_START = 0.0
EIGER_OMEGA_INCREMENT = 1.0
EIGER_NUM_IMAGES_PER_TRIGGER = 1
EIGER_NUM_TRIGGERS = 2000
EIGER_USE_ROI_MODE = False
EIGER_DET_DIST_TO_BEAM_CONVERTER_PATH = "tests/devices/unit_tests/test_lookup_table.txt"
EIGER_1169_FIX = True
