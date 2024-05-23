from typing import TYPE_CHECKING

import numpy as np

from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE

if TYPE_CHECKING:
    from dodal.devices.zocalo import XrcResult

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

OAV_DISPLAY_CONFIG = "tests/devices/unit_tests/test_display.configuration"
OAV_ZOOM_LEVELS = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


ZOC_RESULTS: list["XrcResult"] = [
    {
        "centre_of_mass": [1, 2, 3],
        "max_voxel": [2, 4, 5],
        "max_count": 105062,
        "n_voxels": 38,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
    {
        "centre_of_mass": [2, 3, 4],
        "max_voxel": [2, 4, 5],
        "max_count": 105123,
        "n_voxels": 35,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
    {
        "centre_of_mass": [4, 5, 6],
        "max_voxel": [2, 4, 5],
        "max_count": 102062,
        "n_voxels": 31,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    },
]

ZOC_READING = {
    "zocalo_results-centre_of_mass": {
        "value": np.array([2, 3, 4]),
        "timestamp": 11250827.378482452,
        "alarm_severity": 0,
    },
    "zocalo_results-max_voxel": {
        "value": np.array([2, 4, 5]),
        "timestamp": 11250827.378502235,
        "alarm_severity": 0,
    },
    "zocalo_results-max_count": {
        "value": 105123,
        "timestamp": 11250827.378515247,
        "alarm_severity": 0,
    },
    "zocalo_results-n_voxels": {
        "value": 35,
        "timestamp": 11250827.37852733,
        "alarm_severity": 0,
    },
    "zocalo_results-total_count": {
        "value": 2387574,
        "timestamp": 11250827.378539408,
        "alarm_severity": 0,
    },
    "zocalo_results-bounding_box": {
        "value": np.array([[1, 2, 3], [3, 4, 4]]),
        "timestamp": 11250827.378558964,
        "alarm_severity": 0,
    },
}

ZOC_ISPYB_IDS = {"dcid": 0, "dcgid": 0}
