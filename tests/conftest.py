import logging
import sys
from os import environ, getenv
from unittest.mock import MagicMock, patch

import pytest

from dodal.beamlines import i03
from dodal.log import LOGGER, GELFTCPHandler, set_up_logging_handlers


def pytest_runtest_setup(item):
    if "dodal.beamlines.beamline_utils" in sys.modules:
        sys.modules["dodal.beamlines.beamline_utils"].clear_devices()
        assert sys.modules["dodal.beamlines.beamline_utils"].ACTIVE_DEVICES == {}
    if LOGGER.handlers == []:
        mock_graylog_handler = MagicMock(spec=GELFTCPHandler)
        mock_graylog_handler.return_value.level = logging.DEBUG

        with patch("dodal.log.GELFTCPHandler", mock_graylog_handler):
            set_up_logging_handlers(None, False)


def pytest_runtest_teardown():
    if "dodal.beamlines.beamline_utils" in sys.modules:
        sys.modules["dodal.beamlines.beamline_utils"].clear_devices()


@pytest.fixture
def vfm_mirror_voltages():
    voltages = i03.vfm_mirror_voltages(fake_with_ophyd_sim=True)
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
