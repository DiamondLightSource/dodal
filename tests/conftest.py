import importlib
import logging
import os
import sys
from os import environ, getenv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dodal.beamlines import beamline_utils
from dodal.log import LOGGER, GELFTCPHandler, set_up_all_logging_handlers
from dodal.testing_utils import (
    RE,
    mock_beamline_module_filepaths,
    mock_undulator_dcm,
    mock_vfm_mirror_voltages,
)
from dodal.utils import make_all_devices

__all__ = ["mock_vfm_mirror_voltages", "RE", "mock_undulator_dcm"]


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(request):
    beamline = request.param
    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        bl_mod = importlib.import_module("dodal.beamlines." + beamline)
        importlib.reload(bl_mod)
        mock_beamline_module_filepaths(beamline, bl_mod)
        yield (
            bl_mod,
            make_all_devices(bl_mod, include_skipped=True, fake_with_ophyd_sim=True),
        )
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


s03_epics_server_port = getenv("S03_EPICS_CA_SERVER_PORT")
s03_epics_repeater_port = getenv("S03_EPICS_CA_REPEATER_PORT")

if s03_epics_server_port is not None:
    environ["EPICS_CA_SERVER_PORT"] = s03_epics_server_port
    print(f"[EPICS_CA_SERVER_PORT] = {s03_epics_server_port}")
if s03_epics_repeater_port is not None:
    environ["EPICS_CA_REPEATER_PORT"] = s03_epics_repeater_port
    print(f"[EPICS_CA_REPEATER_PORT] = {s03_epics_repeater_port}")
