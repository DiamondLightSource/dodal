import logging
from pathlib import Path, PosixPath
from typing import cast
from unittest.mock import MagicMock, call, patch

import pytest
from graypy import GELFTCPHandler
from ophyd import log as ophyd_log
from ophyd_async.core import Device, soft_signal_rw

from dodal import log
from dodal.log import (
    ERROR_LOG_BUFFER_LINES,
    LOGGER,
    BeamlineFilter,
    CircularMemoryHandler,
    DodalLogHandlers,
    clear_all_loggers_and_handlers,
    do_default_logging_setup,
    get_logging_file_paths,
    integrate_bluesky_and_ophyd_logging,
    set_up_all_logging_handlers,
)


@pytest.fixture()
def mock_logger():
    with patch("dodal.log.LOGGER") as mock_LOGGER:
        yield mock_LOGGER


@pytest.fixture()
def dodal_logger_for_tests():
    logger = logging.getLogger("Dodal")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    return logger


@patch("dodal.log.StreamHandler", autospec=True)
@patch("dodal.log.GELFTCPHandler", autospec=True)
@patch("dodal.log.TimedRotatingFileHandler", autospec=True)
@patch("dodal.log.CircularMemoryHandler", autospec=True)
def test_handlers_set_at_correct_default_level(
    mock_memory_handler,
    mock_file_handler,
    mock_GELFTCPHandler,
    mock_stream_handler,
    mock_logger: MagicMock,
):
    mock_memory_handler.return_value.level = logging.DEBUG
    mock_file_handler.return_value.level = logging.INFO
    mock_GELFTCPHandler.return_value.level = logging.INFO
    mock_stream_handler.return_value.level = logging.DEBUG
    handlers = set_up_all_logging_handlers(mock_logger, Path(""), "", True, 10000)

    for handler in handlers.values():
        mock_logger.addHandler.assert_any_call(handler)

    handlers["debug_memory_handler"].setLevel.assert_called_once_with(logging.DEBUG)  # type: ignore
    handlers["graylog_handler"].setLevel.assert_called_once_with(logging.INFO)  # type: ignore
    handlers["info_file_handler"].setLevel.assert_any_call(logging.INFO)  # type: ignore
    handlers["info_file_handler"].setLevel.assert_any_call(logging.DEBUG)  # type: ignore
    handlers["stream_handler"].setLevel.assert_called_once_with(logging.INFO)  # type: ignore


@patch("dodal.log.GELFTCPHandler", autospec=True)
def test_dev_mode_sets_correct_graypy_handler(
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    mock_GELFTCPHandler.return_value.level = logging.INFO
    handler_config = set_up_all_logging_handlers(
        mock_logger, Path("tmp/dev"), "dodal.log", True, 10000
    )
    mock_GELFTCPHandler.assert_called_once_with("localhost", 5555)
    _close_all_handlers(handler_config)


@patch("dodal.log.GELFTCPHandler", autospec=True)
def test_prod_mode_sets_correct_graypy_handler(
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    mock_GELFTCPHandler.return_value.level = logging.INFO
    handler_config = set_up_all_logging_handlers(
        mock_logger, Path("tmp/dev"), "dodal.log", False, 10000
    )
    mock_GELFTCPHandler.assert_called_once_with(
        "graylog-log-target.diamond.ac.uk", 12231
    )
    _close_all_handlers(handler_config)


@patch("dodal.log.GELFTCPHandler", autospec=True)
@patch("dodal.log.TimedRotatingFileHandler", autospec=True)
@patch("dodal.log.CircularMemoryHandler", autospec=True)
def test_no_env_variable_sets_correct_file_handler(
    mock_memory_handler,
    mock_file_handler: MagicMock,
    mock_GELFTCPHandler,
    mock_logger: MagicMock,
):
    mock_memory_handler.return_value.level = logging.DEBUG
    mock_file_handler.return_value.level = logging.INFO
    mock_GELFTCPHandler.return_value.level = logging.INFO
    clear_all_loggers_and_handlers()
    logging_file_path, debug_logging_file_path = get_logging_file_paths()
    handler_config = set_up_all_logging_handlers(
        LOGGER,
        logging_file_path,
        "dodal.log",
        True,
        ERROR_LOG_BUFFER_LINES,
        debug_logging_path=debug_logging_file_path,
    )
    integrate_bluesky_and_ophyd_logging(LOGGER)

    expected_calls = [
        call(filename=PosixPath("tmp/dev/dodal.log"), when="MIDNIGHT", backupCount=30),
        call(PosixPath("tmp/dev/debug/dodal.log"), when="H", backupCount=7),
    ]

    mock_file_handler.assert_has_calls(expected_calls, any_order=True)
    _close_all_handlers(handler_config)


def test_beamline_filter_adds_dev_if_no_beamline():
    filter = BeamlineFilter()
    record = MagicMock()
    assert filter.filter(record)
    assert record.beamline == "dev"


@patch("dodal.log.logging.FileHandler.emit")
def test_messages_logged_from_dodal_get_sent_to_graylog_and_file(
    mock_filehandler_emit: MagicMock,
):
    clear_all_loggers_and_handlers()
    assert LOGGER.handlers == []
    mock_graylog_handler_class = MagicMock(spec=GELFTCPHandler)
    mock_graylog_handler_class.return_value.level = logging.DEBUG
    with patch("dodal.log.GELFTCPHandler", mock_graylog_handler_class):
        handlers = set_up_all_logging_handlers(
            LOGGER, Path("tmp/dev"), "dodal.log", False, 10000
        )
    LOGGER.info("test")
    mock_GELFTCPHandler = handlers["graylog_handler"]
    assert mock_GELFTCPHandler is not None
    mock_graylog_handler_class.assert_called_once_with(
        "graylog-log-target.diamond.ac.uk", 12231
    )
    mock_GELFTCPHandler.handle.assert_called()  # type: ignore
    mock_filehandler_emit.assert_called()


@patch("dodal.log.logging.FileHandler.emit")
def test_various_messages_to_graylog_get_beamline_filter(
    mock_filehandler_emit: MagicMock, RE
):
    from os import environ

    if environ.get("BEAMLINE"):
        del environ["BEAMLINE"]
    log.beamline_filter = log.BeamlineFilter()

    def mock_set_up_graylog_handler(logger, host, port):
        graylog_handler = GELFTCPHandler(host, port)
        graylog_handler.emit = MagicMock()
        graylog_handler.addFilter(log.beamline_filter)
        log._add_handler(logger, graylog_handler)
        return graylog_handler

    clear_all_loggers_and_handlers()
    with patch("dodal.log.set_up_graylog_handler", mock_set_up_graylog_handler):
        handlers = set_up_all_logging_handlers(
            LOGGER, Path("tmp/dev"), "dodal.log", True, 10000
        )
        integrate_bluesky_and_ophyd_logging(LOGGER)

    mock_GELFTCPHandler: GELFTCPHandler = handlers["graylog_handler"]
    assert mock_GELFTCPHandler is not None
    assert mock_GELFTCPHandler.host == "localhost"
    assert mock_GELFTCPHandler.port == 5555

    LOGGER.info("test")
    assert isinstance(mock_GELFTCPHandler.emit, MagicMock)
    mock_GELFTCPHandler.emit.assert_called()
    assert mock_GELFTCPHandler.emit.call_args.args[0].beamline == "dev"

    ophyd_log.logger.info("Ophyd log message")
    assert mock_GELFTCPHandler.emit.call_args.args[0].name == "ophyd"
    assert mock_GELFTCPHandler.emit.call_args.args[0].beamline == "dev"

    RE.log.logger.info("RunEngine log message")
    assert mock_GELFTCPHandler.emit.call_args.args[0].name == "bluesky"
    assert mock_GELFTCPHandler.emit.call_args.args[0].beamline == "dev"


@pytest.mark.parametrize(
    "num_info_messages,expected_messages_start_idx",
    [(5, 0), (20, 11), (500, 491)],
)
def test_given_circular_memory_handler_with_varying_number_of_messages_when_record_of_correct_level_comes_in_then_flushed_with_expected_messages(
    num_info_messages, expected_messages_start_idx
):
    target: logging.Handler = MagicMock(spec=logging.Handler)
    circular_handler = CircularMemoryHandler(10, target=target)
    info_messages = [
        logging.LogRecord(f"Info_{i}", logging.INFO, "", 0, None, None, None)
        for i in range(num_info_messages)
    ]
    for message in info_messages:
        circular_handler.emit(message)
    target.handle.assert_not_called()  # type: ignore
    error_message = logging.LogRecord("Error", logging.ERROR, "", 0, None, None, None)
    circular_handler.emit(error_message)
    expected_calls = [
        call(message) for message in info_messages[expected_messages_start_idx:]
    ]
    expected_calls.append(call(error_message))
    assert target.handle.call_count == len(expected_calls)  # type: ignore
    target.handle.assert_has_calls(expected_calls)  # type: ignore


def test_when_circular_memory_handler_closed_then_clears_buffer_and_target():
    circular_handler = CircularMemoryHandler(10, target=MagicMock())
    circular_handler.emit(
        logging.LogRecord("Info", logging.INFO, "", 0, None, None, None)
    )
    assert len(circular_handler.buffer) == 1
    circular_handler.close()
    assert len(circular_handler.buffer) == 0
    assert circular_handler.target is None


async def test_ophyd_async_logger_integrated(caplog, dodal_logger_for_tests):
    integrate_bluesky_and_ophyd_logging(dodal_logger_for_tests)
    test_signal = soft_signal_rw(int, 0, "test_signal")
    await test_signal.connect()
    assert "Connecting to soft://test_signal" in caplog.text


async def test_ophyd_async_logger_configured(dodal_logger_for_tests):
    integrate_bluesky_and_ophyd_logging(dodal_logger_for_tests)
    do_default_logging_setup(True)
    stream_handler: logging.StreamHandler = dodal_logger_for_tests.handlers[0]
    stream_handler.level = logging.DEBUG
    stream_handler.stream.write = MagicMock()
    test_signal_name = "TEST SIGNAL NAME"
    test_device_name = "TEST DEVICE NAME"

    class _Device(Device):
        def __init__(self, name: str = test_device_name) -> None:
            super().__init__(name)
            self.test_signal = soft_signal_rw(int, 0, test_signal_name)

    device = _Device()
    await device.connect()
    assert f"[{test_signal_name}]" in stream_handler.stream.write.call_args.args[0]
    device.log.debug("test message")
    assert f"[{test_device_name}]" in stream_handler.stream.write.call_args.args[0]


def _close_all_handlers(handler_config: DodalLogHandlers):
    for handler in handler_config.values():
        cast(logging.Handler, handler).close()
