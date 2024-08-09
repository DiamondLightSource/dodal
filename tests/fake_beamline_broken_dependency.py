from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.devices.cryostream import CryoStream


def device_x() -> Readable:
    return _mock_with_name("readable")


def device_y() -> EpicsMotor:
    raise AssertionError("Test failure")


def device_z(device_x: Readable, device_y: EpicsMotor) -> CryoStream:
    return _mock_with_name("cryo")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
