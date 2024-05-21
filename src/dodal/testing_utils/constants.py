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
