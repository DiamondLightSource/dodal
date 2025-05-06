from __future__ import annotations

import logging
from collections import deque
from logging import Logger, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from os import environ
from pathlib import Path
from typing import TypedDict

import colorlog
from bluesky.log import logger as bluesky_logger
from graypy import GELFTCPHandler
from ophyd.log import logger as ophyd_logger

LOGGER = logging.getLogger("Dodal")
# Temporarily duplicated https://github.com/bluesky/ophyd-async/issues/550
ophyd_async_logger = logging.getLogger("ophyd_async")
LOGGER.setLevel(logging.DEBUG)

ERROR_LOG_BUFFER_LINES = 20000
INFO_LOG_DAYS = 30
DEBUG_LOG_FILES_TO_KEEP = 7
DEFAULT_GRAYLOG_PORT = 12231

# Temporarily duplicated https://github.com/bluesky/ophyd-async/issues/550
DEFAULT_FORMAT = (
    "%(log_color)s[%(levelname)1.1s %(asctime)s.%(msecs)03d "
    "%(module)s:%(lineno)d] %(message)s"
)

DEFAULT_DATE_FORMAT = "%y%m%d %H:%M:%S"

DEFAULT_LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}


class ColoredFormatterWithDeviceName(colorlog.ColoredFormatter):
    def format(self, record):
        message = super().format(record)
        if device_name := getattr(record, "ophyd_async_device_name", None):
            message = f"[{device_name}]{message}"
        return message


DEFAULT_FORMATTER = ColoredFormatterWithDeviceName(
    fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT, log_colors=DEFAULT_LOG_COLORS
)


class CircularMemoryHandler(logging.Handler):
    """Loosely based on the MemoryHandler, which keeps a buffer and writes it when full
    or when there is a record of specific level. This instead keeps a circular buffer
    that always contains the last {capacity} number of messages, this is only flushed
    when a log of specific {flushLevel} comes in. On flush this buffer is then passed to
    the {target} handler.

    The CircularMemoryHandler becomes the owner of the target handler which will be closed
    on close of this handler.
    """

    def __init__(self, capacity, flushLevel=logging.ERROR, target=None):
        logging.Handler.__init__(self)
        self.buffer: deque[logging.LogRecord] = deque(maxlen=capacity)
        self.flushLevel = flushLevel
        self.target = target

    def emit(self, record):
        self.buffer.append(record)
        if record.levelno >= self.flushLevel:
            self.flush()

    def flush(self):
        """
        Pass the contents of the buffer forward to the target.
        """
        self.acquire()
        try:
            if self.target:
                for record in self.buffer:
                    self.target.handle(record)
        finally:
            self.release()

    def close(self):
        self.acquire()
        try:
            self.buffer.clear()
            if self.target:
                self.target.acquire()
                try:
                    self.target.close()
                finally:
                    self.target.release()
            self.target = None
            logging.Handler.close(self)
        finally:
            self.release()


class BeamlineFilter(logging.Filter):
    beamline: str | None = environ.get("BEAMLINE")

    def filter(self, record):
        record.beamline = self.beamline if self.beamline else "dev"
        return True


beamline_filter = BeamlineFilter()


def clear_all_loggers_and_handlers():
    for handler in LOGGER.handlers:
        handler.close()
    LOGGER.handlers.clear()


def set_beamline(beamline_name: str):
    """Set the beamline on all subsequent log messages."""
    beamline_filter.beamline = beamline_name


class DodalLogHandlers(TypedDict):
    stream_handler: StreamHandler
    graylog_handler: GELFTCPHandler
    info_file_handler: TimedRotatingFileHandler
    debug_memory_handler: CircularMemoryHandler


def _add_handler(logger: logging.Logger, handler: logging.Handler):
    print(f"adding handler {handler} to logger {logger}, at level: {handler.level}")
    handler.setFormatter(DEFAULT_FORMATTER)
    logger.addHandler(handler)


def set_up_graylog_handler(logger: Logger, host: str, port: int):
    """Set up a graylog handler for the logger, at "INFO" level, with the at the
    specified address and host. get_graylog_configuration() can provide these values
    for prod and dev respectively.
    """
    graylog_handler = GELFTCPHandler(host, port)
    graylog_handler.setLevel(logging.INFO)
    _add_handler(logger, graylog_handler)
    return graylog_handler


def set_up_INFO_file_handler(logger, path: Path, filename: str):
    """Set up a file handler for the logger, at INFO level, which will keep 30 days
    of logs, rotating once per day. Creates the directory if necessary."""
    print(f"Logging to INFO file handler {path / filename}")
    path.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=path / filename, when="MIDNIGHT", backupCount=INFO_LOG_DAYS
    )
    file_handler.setLevel(logging.INFO)
    _add_handler(logger, file_handler)
    return file_handler


def set_up_DEBUG_memory_handler(
    logger: Logger, path: Path, filename: str, capacity: int
):
    """Set up a Memory handler which holds 200k lines, and writes them to an hourly
    log file when it sees a message of severity ERROR. Creates the directory if
    necessary"""
    debug_path = path / "debug"
    print(f"Logging to DEBUG handler {debug_path / filename}")
    debug_path.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=debug_path / filename, when="H", backupCount=DEBUG_LOG_FILES_TO_KEEP
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(DEFAULT_FORMATTER)
    memory_handler = CircularMemoryHandler(
        capacity=capacity,
        flushLevel=logging.ERROR,
        target=file_handler,
    )
    memory_handler.setLevel(logging.DEBUG)
    memory_handler.addFilter(beamline_filter)
    _add_handler(logger, memory_handler)
    return memory_handler


def set_up_stream_handler(logger: Logger):
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    _add_handler(logger, stream_handler)
    return stream_handler


def set_up_all_logging_handlers(
    logger: Logger,
    logging_path: Path,
    filename: str,
    dev_mode: bool,
    error_log_buffer_lines: int,
    graylog_port: int | None = None,
    debug_logging_path: Path | None = None,
) -> DodalLogHandlers:
    """Set up the default logging environment.
    Args:
        logger:                 the logging.Logger object to apply all the handlers to.
        logging_path:           The location to store log files.
        filename:               The log filename.
        dev_mode:               If true, will log to graylog on localhost instead of
                                production. Defaults to False.
        error_log_buffer_lines: Number of lines for the CircularMemoryHandler to keep in
                                buffer and write to file when encountering an error message.
        graylog_port:           The port to send graylog messages to, if None uses the
                                default dodal port
        debug_logging_path:     The location to store debug log files, if None uses `logging_path`
    Returns:
        A DodaLogHandlers TypedDict with the created handlers.
    """
    handlers: DodalLogHandlers = {
        "stream_handler": set_up_stream_handler(logger),
        "graylog_handler": set_up_graylog_handler(
            logger, *get_graylog_configuration(dev_mode, graylog_port)
        ),
        "info_file_handler": set_up_INFO_file_handler(logger, logging_path, filename),
        "debug_memory_handler": set_up_DEBUG_memory_handler(
            logger, debug_logging_path or logging_path, filename, error_log_buffer_lines
        ),
    }

    return handlers


def integrate_bluesky_and_ophyd_logging(parent_logger: logging.Logger):
    for logger in [ophyd_logger, bluesky_logger, ophyd_async_logger]:
        logger.parent = parent_logger
        logger.setLevel(logging.DEBUG)


def do_default_logging_setup(dev_mode=False, graylog_port: int | None = None):
    logging_path, debug_logging_path = get_logging_file_paths()
    set_up_all_logging_handlers(
        LOGGER,
        logging_path,
        "dodal.log",
        dev_mode,
        ERROR_LOG_BUFFER_LINES,
        graylog_port,
        debug_logging_path,
    )
    integrate_bluesky_and_ophyd_logging(LOGGER)


def get_logging_file_paths() -> tuple[Path, Path]:
    """Get the directories to write log files to.

    If on a beamline, this will return '/dls_sw/$BEAMLINE/logs/bluesky' based on the
    BEAMLINE environment variable. If no environment variable is found it will default
    to the tmp/dev directory.

    Returns:
        tuple[Path, Path]: Paths to the standard log file and to the debug log file,
                           for the file handlers to write to
    """
    beamline: str | None = environ.get("BEAMLINE")

    if beamline:
        logging_path = Path("/dls_sw/" + beamline + "/logs/bluesky/")
        debug_logging_path = Path("/dls/tmp/" + beamline + "/logs/bluesky/")
    else:
        logging_path = Path("./tmp/dev/")
        debug_logging_path = Path("./tmp/dev/")
    return logging_path, debug_logging_path


def get_graylog_configuration(
    dev_mode: bool, graylog_port: int | None = None
) -> tuple[str, int]:
    """Get the host and port for the graylog handler.

    If running in dev mode, this switches to localhost. Otherwise it publishes to the
    DLS graylog.

    Returns:
        (host, port): A tuple of the relevant host and port for graylog.
    """
    if dev_mode:
        return "localhost", 5555
    else:
        return "graylog-log-target.diamond.ac.uk", graylog_port or DEFAULT_GRAYLOG_PORT
