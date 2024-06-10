import asyncio
import importlib
import logging
import os
import sys
import time
from os import environ, getenv
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device

from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils
from dodal.devices.focusing_mirror import VFMMirrorVoltages
from dodal.log import LOGGER, GELFTCPHandler, set_up_all_logging_handlers
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
def module_and_devices_for_beamline(request):
    beamline = request.param
    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        bl_mod = importlib.import_module("dodal.beamlines." + beamline)
        importlib.reload(bl_mod)
        mock_beamline_module_filepaths(beamline, bl_mod)
        devices, _ = make_all_devices(
            bl_mod,
            include_skipped=True,
            fake_with_ophyd_sim=True,
        )
        yield (bl_mod, devices)
        beamline_utils.clear_devices()
        del bl_mod


def pytest_runtest_setup(item):
    beamline_utils.clear_devices()
    if LOGGER.handlers == []:
        mock_graylog_handler = MagicMock(spec=GELFTCPHandler)
        mock_graylog_handler.return_value.level = logging.DEBUG

        with patch("dodal.log.GELFTCPHandler", mock_graylog_handler):
            set_up_all_logging_handlers(
                LOGGER, Path("./tmp/dev"), "dodal.log", True, 10000
            )


def pytest_runtest_teardown():
    if "dodal.beamlines.beamline_utils" in sys.modules:
        sys.modules["dodal.beamlines.beamline_utils"].clear_devices()


@pytest.fixture
def vfm_mirror_voltages() -> VFMMirrorVoltages:
    voltages = cast(
        VFMMirrorVoltages,
        make_fake_device(VFMMirrorVoltages)(
            name="vfm_mirror_voltages",
            prefix="BL-I03-MO-PSU-01:",
            daq_configuration_path=i03.DAQ_CONFIGURATION_PATH,
        ),
    )
    voltages.voltage_lookup_table_path = "tests/test_data/test_mirror_focus.json"
    return voltages


s03_epics_server_port = getenv("S03_EPICS_CA_SERVER_PORT")
s03_epics_repeater_port = getenv("S03_EPICS_CA_REPEATER_PORT")

if s03_epics_server_port is not None:
    environ["EPICS_CA_SERVER_PORT"] = s03_epics_server_port
    print(f"[EPICS_CA_SERVER_PORT] = {s03_epics_server_port}")
if s03_epics_repeater_port is not None:
    environ["EPICS_CA_REPEATER_PORT"] = s03_epics_repeater_port
    print(f"[EPICS_CA_REPEATER_PORT] = {s03_epics_repeater_port}")


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
