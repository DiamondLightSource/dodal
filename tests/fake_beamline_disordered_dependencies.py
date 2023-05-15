from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.devices.cryostream import Cryo


def device_z(device_x: Readable, device_y: EpicsMotor) -> Cryo:
    return _mock_with_name("cryo")


def device_x() -> Readable:
    return _mock_with_name("readable")


def device_y() -> EpicsMotor:
    return _mock_with_name("motor")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
