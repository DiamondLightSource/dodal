import importlib
import os
import re
import socket
import string
from collections.abc import Callable
from dataclasses import dataclass
from os import environ
from types import ModuleType
from typing import (
    TypeAlias,
    TypeVar,
)

from bluesky.protocols import (
    Checkable,
    Configurable,
    Flyable,
    HasHints,
    HasName,
    HasParent,
    Movable,
    Pausable,
    Readable,
    Stageable,
    Stoppable,
    Subscribable,
    Triggerable,
    WritesExternalAssets,
)
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device

import dodal.log

#: Protocols defining interface to hardware
BLUESKY_PROTOCOLS = [
    Checkable,
    Flyable,
    HasHints,
    HasName,
    HasParent,
    Movable,
    Pausable,
    Readable,
    Stageable,
    Stoppable,
    Subscribable,
    WritesExternalAssets,
    Configurable,
    Triggerable,
]

AnyDevice: TypeAlias = OphydV1Device | OphydV2Device
V1DeviceFactory: TypeAlias = Callable[..., OphydV1Device]
V2DeviceFactory: TypeAlias = Callable[..., OphydV2Device]
AnyDeviceFactory: TypeAlias = V1DeviceFactory | V2DeviceFactory


def get_beamline_name(default: str | None = None) -> str:
    beamline_name = environ.get("BEAMLINE") or default
    if beamline_name is None:
        raise ValueError("Set BEAMLINE environment variable or provide default.")
    return beamline_name


def is_test_mode() -> bool:
    return environ.get("DODAL_TEST_MODE") == "true"


def get_hostname() -> str:
    return socket.gethostname().split(".")[0]


@dataclass
class BeamlinePrefix:
    ixx: str
    suffix: str | None = None

    def __post_init__(self):
        self.suffix = self.ixx[0].upper() if not self.suffix else self.suffix
        self.beamline_prefix = f"BL{self.ixx[1:3]}{self.suffix}"
        self.insertion_prefix = f"SR{self.ixx[1:3]}{self.suffix}"
        self.frontend_prefix = f"FE{self.ixx[1:3]}{self.suffix}"


T = TypeVar("T", bound=AnyDevice)


def get_beamline_based_on_environment_variable() -> ModuleType:
    """Gets the dodal module for the current beamline, as specified by the
    BEAMLINE environment variable.
    """
    beamline = get_beamline_name("")

    if beamline == "":
        raise ValueError(
            "Cannot determine beamline - BEAMLINE environment variable not set."
        )

    beamline = beamline.replace("-", "_")
    valid_characters = string.ascii_letters + string.digits + "_"

    if (
        len(beamline) == 0
        or beamline[0] not in string.ascii_letters
        or any(c not in valid_characters for c in beamline)
    ):
        raise ValueError(
            f"Invalid BEAMLINE variable - module name is not a permissible python module name, got '{beamline}'"
        )

    try:
        return importlib.import_module(f"dodal.beamlines.{beamline}")
    except ImportError as e:
        raise ValueError(
            f"Failed to import beamline-specific dodal module 'dodal.beamlines.{beamline}'."
            " Ensure your BEAMLINE environment variable is set to a known instrument."
        ) from e


def _find_next_run_number_from_files(file_names: list[str]) -> int:
    valid_numbers = []

    for file_name in file_names:
        file_name = file_name.strip(".nxs")
        # Give warning if nexus file name isn't in expcted format, xxx_number.nxs
        match = re.search(r"_\d+$", file_name)
        if match is not None:
            valid_numbers.append(int(re.findall(r"\d+", file_name)[-1]))
        else:
            dodal.log.LOGGER.warning(
                f"Identified nexus file {file_name} with unexpected format"
            )
    return max(valid_numbers) + 1 if valid_numbers else 1


def get_run_number(directory: str, prefix: str = "") -> int:
    """Looks at the numbers coming from all nexus files with the format
    "{prefix}_(any number}.nxs", and returns the highest number + 1, or 1 if there are
    no matching numbers found. If no prefix is given, considers all files in the dir.
    """
    nexus_file_names = [
        file
        for file in os.listdir(directory)
        if file.endswith(".nxs") and file.startswith(prefix)
    ]

    if len(nexus_file_names) == 0:
        return 1
    else:
        return _find_next_run_number_from_files(nexus_file_names)
