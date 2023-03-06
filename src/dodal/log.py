from __future__ import annotations

import logging
from os import environ
from pathlib import Path
from typing import List, Optional

from bluesky.log import config_bluesky_logging
from bluesky.log import logger as bluesky_logger
from ophyd.log import config_ophyd_logging
from ophyd.log import logger as ophyd_logger

LOGGER = logging.getLogger("Dodal")
LOGGER.setLevel(logging.DEBUG)  # default logger to log everything
ophyd_logger.parent = LOGGER
bluesky_logger.parent = LOGGER


def set_up_logging_handlers(
    logging_level: Optional[str] = "INFO", dev_mode: bool = False
) -> List[logging.Handler]:
    """Set up the logging level and instances for user chosen level of logging.

    Mode defaults to production and can be switched to dev with the --dev flag on run.
    """
    logging_level = logging_level if logging_level else "INFO"
    file_path = Path(_get_logging_file_path(), "dodal.txt")
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s %(module)s %(levelname)s: %(message)s"
    )
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(filename=file_path),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        LOGGER.addHandler(handler)

    # for assistance in debugging
    if dev_mode:
        set_seperate_ophyd_bluesky_files(
            logging_level=logging_level, logging_path=_get_logging_file_path()
        )

    return handlers


def _get_logging_file_path() -> Path:
    """Get the path to write the artemis log files to.

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
    return logging_path


def set_seperate_ophyd_bluesky_files(logging_level: str, logging_path: Path) -> None:
    """Set file path for the file handlder to the individual Bluesky and Ophyd loggers.

    These provide seperate, nicely formatted logs in the same dir as the dodal log
    file for each individual module.
    """
    bluesky_file_path: Path = Path(logging_path, "bluesky.log")
    ophyd_file_path: Path = Path(logging_path, "ophyd.log")

    config_bluesky_logging(file=str(bluesky_file_path), level=logging_level)
    config_ophyd_logging(file=str(ophyd_file_path), level=logging_level)
