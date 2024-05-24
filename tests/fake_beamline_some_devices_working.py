from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd_async.epics.motion import Motor

from dodal.devices.undulator import Undulator


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> Motor:
    raise TimeoutError


def device_c() -> Undulator:
    return _mock_with_name("undulator")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
