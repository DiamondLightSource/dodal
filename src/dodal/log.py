from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from os import environ
from pathlib import Path
from typing import List, Optional, Tuple

from bluesky.log import config_bluesky_logging
from bluesky.log import logger as bluesky_logger
from graypy import GELFTCPHandler
from ophyd.log import config_ophyd_logging
from ophyd.log import logger as ophyd_logger

LOGGER = logging.getLogger("Dodal")
LOGGER.setLevel(logging.DEBUG)
ophyd_logger.parent = LOGGER
bluesky_logger.parent = LOGGER

DEFAULT_FORMATTER = logging.Formatter(
    "[%(asctime)s] %(name)s %(module)s %(levelname)s: %(message)s"
)


class EnhancedRollingFileHandler(TimedRotatingFileHandler):
    """Combines features of TimedRotatingFileHandler and RotatingFileHandler"""

    def __init__(
        self,
        filename,
        when="MIDNIGHT",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        maxBytes=1e8,
    ):
        TimedRotatingFileHandler.__init__(
            self, filename, when, interval, backupCount, encoding, delay, utc
        )
        self.maxBytes = maxBytes

    def shouldRollover(self, record):
        """
        Check file size and times to see if rollover should occur
        """
        if self.stream is None:  # Stream may not have been created
            self.stream = self._open()
        if self.maxBytes > 0:  # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return super().shouldRollover(record)


class BeamlineFilter(logging.Filter):
    beamline: Optional[str] = environ.get("BEAMLINE")

    def filter(self, record):
        record.beamline = self.beamline if self.beamline else "dev"
        return True


beamline_filter = BeamlineFilter()


def set_beamline(beamline_name: str):
    """Set the beamline on all subsequent log messages."""
    beamline_filter.beamline = beamline_name


def _add_handler(handler: logging.Handler, logging_level: str):
    handler.setFormatter(DEFAULT_FORMATTER)
    handler.setLevel(logging_level)
    LOGGER.addHandler(handler)


def set_up_graylog_handler(logging_level: str, dev_mode: bool = False):
    """Set up a graylog handler for the logger
    Args:
        logging_level: The level of logs that should be saved to graylog. Defaults to INFO.
        dev_mode: True if in dev mode, will log to a local graylog instance in dev. Defaults to False.
    """
    graylog_host, graylog_port = _get_graylog_configuration(dev_mode)
    graylog_handler = GELFTCPHandler(graylog_host, graylog_port)
    _add_handler(graylog_handler, logging_level)
    LOGGER.addFilter(beamline_filter)

    # Warn users if trying to run in prod in debug mode
    if not dev_mode and logging_level == "DEBUG":
        LOGGER.warning(
            'STARTING HYPERION IN DEBUG WITHOUT "--dev" WILL FLOOD PRODUCTION GRAYLOG'
            " WITH MESSAGES. If you really need debug messages, set up a"
            " local graylog instead!\n"
        )
    return graylog_handler


def set_up_file_handler(
    logging_level: str, dev_mode: bool = False, logging_path: Optional[Path] = None
):
    """Set up a file handler for the logger
    Args:
        logging_level: The level of logs that should be saved to file/graylog. Defaults to INFO.
        dev_mode: True if in dev mode, will log separate ophyd/bluesky files in dev. Defaults to False.
        logging_path: The location to store log files, if left as None then puts them in the default location.
    """
    if not logging_path:
        logging_path = _get_logging_file_path()
        print(f"Logging to {logging_path}")
    file_handler = EnhancedRollingFileHandler(filename=logging_path)
    _add_handler(file_handler, logging_level)

    # for assistance in debugging
    if dev_mode:
        set_seperate_ophyd_bluesky_files(
            logging_level=logging_level, logging_path=logging_path.parent
        )

    return file_handler


def set_up_logging_handlers(
    logging_level: Optional[str] = "INFO",
    dev_mode: bool = False,
    logging_path: Optional[Path] = None,
    file_handler_logging_level: Optional[str] = None,
) -> List[logging.Handler]:
    """Set up the default logging environment.
    Args:
        logging_level: The level of logs that should be saved to file/graylog. Defaults to INFO.
        dev_mode: True if in dev mode, will not log to graylog in dev. Defaults to False.
        logging_path: The location to store log files, if left as None then puts them in the default location.
    """
    logging_level = logging_level if logging_level else "INFO"
    stream_handler = logging.StreamHandler()
    _add_handler(stream_handler, logging_level)
    graylog_handler = set_up_graylog_handler(logging_level, dev_mode)
    file_handler_logging_level = (
        file_handler_logging_level if file_handler_logging_level else logging_level
    )
    file_handler = set_up_file_handler(
        file_handler_logging_level, dev_mode, logging_path
    )

    return [stream_handler, graylog_handler, file_handler]


def _get_logging_file_path() -> Path:
    """Get the path to write the hyperion log files to.

    If on a beamline, this will be written to the according area depending on the
    BEAMLINE envrionment variable. If no envrionment variable is found it will default
    it to the tmp/dev directory.

    Returns:
        logging_path (Path): Path to the log file for the file handler to write to.
    """
    beamline: Optional[str] = environ.get("BEAMLINE")
    logging_path: Path

    if beamline:
        logging_path = Path("/dls_sw/" + beamline + "/logs/bluesky/")
    else:
        logging_path = Path("./tmp/dev/")

    Path(logging_path).mkdir(parents=True, exist_ok=True)
    return logging_path / Path("dodal.txt")


def set_seperate_ophyd_bluesky_files(logging_level: str, logging_path: Path) -> None:
    """Set file path for the file handlder to the individual Bluesky and Ophyd loggers.

    These provide seperate, nicely formatted logs in the same dir as the dodal log
    file for each individual module.
    """
    bluesky_file_path: Path = Path(logging_path, "bluesky.log")
    ophyd_file_path: Path = Path(logging_path, "ophyd.log")

    config_bluesky_logging(file=str(bluesky_file_path), level=logging_level)
    config_ophyd_logging(file=str(ophyd_file_path), level=logging_level)


def _get_graylog_configuration(dev_mode: bool) -> Tuple[str, int]:
    """Get the host and port for the  graylog interaction.

    If running on dev mode, this switches to localhost. Otherwise it publishes to the
    dls graylog.

    Returns:
        (host,port): A tuple of the relevent host and port for graylog.
    """
    if dev_mode:
        return "localhost", 5555
    else:
        return "graylog2.diamond.ac.uk", 12218
