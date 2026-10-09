from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dodal.log import LOGGER, GELFTCPHandler, logging, set_up_all_logging_handlers
from dodal.utils import BeamlinePrefix


def reset_logs():
    old_handlers = list(LOGGER.handlers)
    for handler in old_handlers:
        handler.close()
        LOGGER.removeHandler(handler)

    mock_graylog_handler_class = MagicMock(spec=GELFTCPHandler)
    mock_graylog_handler_class.return_value.level = logging.DEBUG
    with patch("dodal.log.GELFTCPHandler", mock_graylog_handler_class):
        set_up_all_logging_handlers(LOGGER, Path("./tmp/dev"), "dodal.log", True, 10000)
    return mock_graylog_handler_class


@pytest.mark.parametrize(
    "ixx, suffix, expected_beamline_suffix, expected_beamline_prefix,"
    "expected_insertion_prefix, expected_frontend_prefix",
    [
        ("i05", None, "I", "BL05I", "SR05I", "FE05I"),
        ("i05-1", None, "I", "BL05I", "SR05I", "FE05I"),
        ("b07", "I", "I", "BL07I", "SR07I", "FE07I"),
        ("b07", "J", "J", "BL07J", "SR07J", "FE07J"),
        ("i07", "K", "K", "BL07K", "SR07K", "FE07K"),
        ("b07-1", "I", "I", "BL07I", "SR07I", "FE07I"),
        ("b07-1", "J", "J", "BL07J", "SR07J", "FE07J"),
        ("b07-1", "C", "C", "BL07C", "SR07C", "FE07C"),
    ],
)
def test_beamline_prefix(
    ixx,
    suffix,
    expected_beamline_suffix,
    expected_beamline_prefix,
    expected_insertion_prefix,
    expected_frontend_prefix,
):
    blp = BeamlinePrefix(ixx, suffix)
    assert blp.suffix == expected_beamline_suffix
    assert blp.beamline_prefix == expected_beamline_prefix
    assert blp.insertion_prefix == expected_insertion_prefix
    assert blp.frontend_prefix == expected_frontend_prefix
