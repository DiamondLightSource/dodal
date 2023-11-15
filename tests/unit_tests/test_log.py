import logging
from functools import partial
from logging import LogRecord
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dodal import log
from dodal.log import EnhancedRollingFileHandler, GELFTCPHandler


def get_mock_streamhandler(level=logging.INFO):
    sh = MagicMock(spec=logging.StreamHandler)
    sh.level = level
    return sh


@pytest.fixture()
def mock_logger():
    with patch("dodal.log.LOGGER") as mock_LOGGER:
        yield mock_LOGGER
        log.beamline = None


@patch("dodal.log.GELFTCPHandler", spec=GELFTCPHandler)
@patch("dodal.log.logging")
@patch("dodal.log.EnhancedRollingFileHandler", spec=EnhancedRollingFileHandler)
def test_handlers_set_at_correct_default_level(
    mock_enhanced_log,
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    mock_logging.StreamHandler = get_mock_streamhandler
    mock_GELFTCPHandler.return_value.level = 20
    mock_enhanced_log.return_value.level = 20
    handlers = log.set_up_logging_handlers(None, False, logger=mock_logger)

    for handler in handlers:
        mock_logger.addHandler.assert_any_call(handler)
        handler.setLevel.assert_called_once_with("INFO")


@patch("dodal.log.GELFTCPHandler", spec=GELFTCPHandler)
@patch("dodal.log.logging")
@patch("dodal.log.EnhancedRollingFileHandler", spec=EnhancedRollingFileHandler)
def test_handlers_set_at_correct_debug_level(
    mock_enhanced_log,
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    mock_logging.StreamHandler = partial(get_mock_streamhandler, 10)
    mock_GELFTCPHandler.return_value.level = 10
    mock_enhanced_log.return_value.level = 10
    handlers = log.set_up_logging_handlers("DEBUG", True, logger=mock_logger)

    for handler in handlers:
        mock_logger.addHandler.assert_any_call(handler)
        handler.setLevel.assert_called_once_with("DEBUG")


@patch("dodal.log.GELFTCPHandler", spec=GELFTCPHandler)
@patch("dodal.log.logging")
def test_dev_mode_sets_correct_graypy_handler(
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    log.set_up_logging_handlers(None, True, logger=mock_logger)
    mock_GELFTCPHandler.assert_called_once_with("localhost", 5555)


@patch("dodal.log.GELFTCPHandler", spec=GELFTCPHandler)
@patch("dodal.log.logging")
def test_prod_mode_sets_correct_graypy_handler(
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    log.set_up_logging_handlers(None, False, logger=mock_logger)
    mock_GELFTCPHandler.assert_called_once_with("graylog2.diamond.ac.uk", 12218)


@patch("dodal.log.GELFTCPHandler")
@patch("dodal.log.logging")
@patch("dodal.log.EnhancedRollingFileHandler")
def test_no_env_variable_sets_correct_file_handler(
    mock_enhanced_log,
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    log.set_up_logging_handlers(None, True, logger=mock_logger)
    mock_enhanced_log.assert_called_once_with(filename=Path("./tmp/dev/dodal.txt"))


@patch("dodal.log.GELFTCPHandler")
@patch("dodal.log.logging")
def test_setting_debug_in_prod_gives_warning(
    mock_logging,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    warning_string = (
        'STARTING HYPERION IN DEBUG WITHOUT "--dev" WILL FLOOD PRODUCTION '
        "GRAYLOG WITH MESSAGES. If you really need debug messages, set up a local "
        "graylog instead!\n"
    )
    log.set_up_logging_handlers("DEBUG", False, logger=mock_logger)
    mock_logger.warning.assert_any_call(warning_string)


def test_beamline_filter_adds_dev_if_no_beamline():
    filter = log.BeamlineFilter()
    record = MagicMock()
    assert filter.filter(record)
    assert record.beamline == "dev"


@patch("dodal.log.logging.FileHandler.emit")
def test_messages_logged_from_dodal_get_sent_to_graylog_and_file(
    mock_filehandler_emit: MagicMock,
):
    for handler in log.LOGGER.handlers:
        handler.close()
    log.LOGGER.handlers = []
    mock_graylog_handler_class = MagicMock(spec=GELFTCPHandler)
    mock_graylog_handler_class.return_value.level = logging.DEBUG
    handlers = [None, None, None]
    with patch("dodal.log.GELFTCPHandler", mock_graylog_handler_class):
        handlers = log.set_up_logging_handlers(None, False)
    logger = log.LOGGER
    logger.info("test")
    mock_GELFTCPHandler = handlers[1]
    assert mock_GELFTCPHandler is not None
    mock_graylog_handler_class.assert_called_once_with("graylog2.diamond.ac.uk", 12218)
    mock_GELFTCPHandler.handle.assert_called()
    mock_filehandler_emit.assert_called()


def test_when_EnhancedRollingFileHandler_reaches_max_size_then_rolls_over():
    rolling_file_handler = log.EnhancedRollingFileHandler("test", delay=True)
    mock_stream = MagicMock()
    mock_stream.tell.return_value = 1e8
    rolling_file_handler._open = MagicMock(return_value=mock_stream)

    assert rolling_file_handler.shouldRollover(
        LogRecord("test", 0, "", 0, None, None, None)
    )


def test_when_EnhancedRollingFileHandler_not_at_max_size_then_no_roll_over():
    rolling_file_handler = log.EnhancedRollingFileHandler("test", delay=True)
    mock_stream = MagicMock()
    mock_stream.tell.return_value = 0
    rolling_file_handler._open = MagicMock(return_value=mock_stream)

    assert not rolling_file_handler.shouldRollover(
        LogRecord("test", 0, "", 0, None, None, None)
    )
