from __future__ import annotations

import logging
from logging import Logger
from logging.handlers import MemoryHandler, TimedRotatingFileHandler
from os import environ
from pathlib import Path
from typing import Optional, Tuple, TypedDict

from bluesky.log import logger as bluesky_logger
from graypy import GELFTCPHandler
from ophyd.log import logger as ophyd_logger

LOGGER = logging.getLogger("Dodal")
LOGGER.setLevel("DEBUG")

ophyd_logger.setLevel("DEBUG")
ophyd_logger.parent = LOGGER
bluesky_logger.setLevel("DEBUG")
bluesky_logger.parent = LOGGER

DEFAULT_FORMATTER = logging.Formatter(
    "[%(asctime)s] %(name)s %(module)s %(levelname)s: %(message)s"
)
ERROR_LOG_BUFFER_LINES = 200000


class BeamlineFilter(logging.Filter):
    beamline: Optional[str] = environ.get("BEAMLINE")

    def filter(self, record):
        record.beamline = self.beamline if self.beamline else "dev"
        return True


beamline_filter = BeamlineFilter()


class DodalLogHandlers(TypedDict):
    stream_handler: logging.Handler
    graylog_handler: logging.Handler
    info_file_handler: logging.Handler
    debug_memory_handler: logging.Handler


def set_beamline(beamline_name: str):
    """Set the beamline on all subsequent log messages."""
    beamline_filter.beamline = beamline_name


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
    _add_handler(logger, graylog_handler)
    return graylog_handler


def set_up_INFO_file_handler(logger, path: Path, filename: str):
    """Set up a file handler for the logger, at INFO level, which will keep 30 days
    of logs, rotating once per day. Creates the directory if necessary."""
    print(f"Logging to {path/filename}")
    path.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=path / filename, when="MIDNIGHT", backupCount=30
    )
    _add_handler(logger, file_handler)
    return file_handler


def set_up_DEBUG_memory_handler(
    logger: Logger, path: Path, filename: str, capacity: int
):
    """Set up a Memory handler which holds 200k lines, and writes them to an hourly
    log file when it sees a message of severity ERROR. Creates the directory if
    necessary"""
    print(f"Logging to {path/filename}")
    debug_path = path / "debug"
    debug_path.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(filename=debug_path / filename, when="H")
    memory_handler = MemoryHandler(
        capacity=capacity, flushLevel=logging.ERROR, target=file_handler
    )
    memory_handler.addFilter(beamline_filter)
    _add_handler(logger, memory_handler)
    return memory_handler


def set_up_stream_handler(logger: Logger):
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel("DEBUG")
    _add_handler(logger, stream_handler)
    return stream_handler


def set_up_all_logging_handlers(
    logger: Logger,
    logging_path: Path,
    filename: str,
    dev_mode: bool = False,
    error_log_buffer_lines=ERROR_LOG_BUFFER_LINES,
) -> DodalLogHandlers:
    """Set up the default logging environment.
    Args:
        logger:                 the logging.Logger object to apply all the handlers to.
        logging_path:           The location to store log files.
        filename:               The log filename.
        dev_mode:               If true, will log to graylog on localhost instead of
                                production. Defaults to False.
        error_log_buffer_lines: Number of lines for the MemoryHandler to keep in buffer
                                and write to file when encountering an error message.
    Returns:
        A DodaLogHandlers TypedDict with the created handlers.
    """

    handlers: DodalLogHandlers = {
        "stream_handler": set_up_stream_handler(logger),
        "graylog_handler": set_up_graylog_handler(
            logger, *get_graylog_configuration(dev_mode)
        ),
        "info_file_handler": set_up_INFO_file_handler(logger, logging_path, filename),
        "debug_memory_handler": set_up_DEBUG_memory_handler(
            logger, logging_path, filename, error_log_buffer_lines
        ),
    }

    return handlers


def get_logging_file_path() -> Path:
    """Get the directory to write log files to.

    If on a beamline, this will return '/dls_sw/$BEAMLINE/logs/bluesky' based on the
    BEAMLINE envrionment variable. If no envrionment variable is found it will default
    to the tmp/dev directory.

    Returns:
        logging_path (Path): Path to the log directory for the file handlers to write to.
    """
    beamline: Optional[str] = environ.get("BEAMLINE")
    logging_path: Path

    if beamline:
        logging_path = Path("/dls_sw/" + beamline + "/logs/bluesky/")
    else:
        logging_path = Path("./tmp/dev/")
    return logging_path


def get_graylog_configuration(dev_mode: bool) -> Tuple[str, int]:
    """Get the host and port for the graylog handler.

    If running in dev mode, this switches to localhost. Otherwise it publishes to the
    DLS graylog.

    Returns:
        (host, port): A tuple of the relevant host and port for graylog.
    """
    if dev_mode:
        return "localhost", 5555
    else:
        return "graylog2.diamond.ac.uk", 12218
