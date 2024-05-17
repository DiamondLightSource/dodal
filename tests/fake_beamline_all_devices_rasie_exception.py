from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor
from ophyd.utils import (
    DestroyedError,
    DisconnectedError,
    UnknownStatusFailure,
    WaitTimeoutError,
)

from dodal.devices.cryostream import Cryo


def device_a() -> Readable:
    raise DestroyedError


def device_b() -> EpicsMotor:
    raise DisconnectedError


def device_c() -> Cryo:
    raise UnknownStatusFailure


def not_device() -> int:
    raise WaitTimeoutError


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
