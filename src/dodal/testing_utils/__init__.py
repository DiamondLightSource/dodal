import asyncio
import time

import pytest
from bluesky.run_engine import RunEngine

from dodal.devices.focusing_mirror import get_mock_voltages
from dodal.devices.undulator_dcm import get_mock_device as get_mock_undulator_dcm

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


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := MOCK_ATTRIBUTES_TABLE.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]


@pytest.fixture
async def RE():
    RE = RunEngine()
    # make sure the event loop is thoroughly up and running before we try to create
    # any ophyd_async devices which might need it
    timeout = time.monotonic() + 1
    while not RE.loop.is_running():
        await asyncio.sleep(0)
        if time.monotonic() > timeout:
            raise TimeoutError("This really shouldn't happen but just in case...")
    yield RE


@pytest.fixture
def mock_vfm_mirror_voltages():
    return get_mock_voltages(MOCK_DAQ_CONFIG_PATH)


@pytest.fixture
async def mock_undulator_dcm():
    return await get_mock_undulator_dcm(ID_GAP_LOOKUP_TABLE_PATH, MOCK_DAQ_CONFIG_PATH)
