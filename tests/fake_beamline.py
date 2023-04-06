from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.devices.cryostream import Cryo


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> EpicsMotor:
    return _mock_with_name("motor")


def device_c() -> Cryo:
    return _mock_with_name("cryo")


def not_device() -> int:
    return 5


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
