import importlib
import os
from unittest.mock import patch

import pytest

from dodal.common.beamlines import beamline_utils
from dodal.utils import make_all_devices

MOCK_DAQ_CONFIG_PATH = "tests/devices/unit_tests/test_daq_configuration"
mock_paths = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"),
    ("DISPLAY_CONFIG", "tests/devices/unit_tests/test_display.configuration"),
]

mock_attributes_table = {
    "i03": mock_paths,
    "s03": mock_paths,
    "i04": mock_paths,
    "s04": mock_paths,
}


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := mock_attributes_table.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]


@pytest.fixture(scope="function")
def module_and_devices_for_beamline_device_factory(request):
    beamline = request.param
    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        beamline_module = importlib.import_module("dodal.beamlines." + beamline)
        importlib.reload(beamline_module)
        mock_beamline_module_filepaths(beamline, beamline_module)
        devices, _ = make_all_devices(beamline_module)
        yield (beamline_module, devices)
        beamline_utils.clear_devices()
        del beamline_module
