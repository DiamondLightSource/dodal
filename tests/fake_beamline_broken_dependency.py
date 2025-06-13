from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor

from dodal.devices.cryostream import CryoStream


def device_x() -> Readable:
    return _mock_with_name("readable")


def device_y() -> Motor:
    raise AssertionError("Test failure")


def device_z(device_x: Readable, device_y: Motor) -> CryoStream:
    return _mock_with_name("cryo")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
