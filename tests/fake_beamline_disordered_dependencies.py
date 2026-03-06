from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor

from dodal.devices.cryostream import OxfordCryoStream


def device_z(device_x: Readable, device_y: Motor) -> OxfordCryoStream:
    return _mock_with_name("cryo")


def device_x() -> Readable:
    return _mock_with_name("readable")


def device_y() -> Motor:
    return _mock_with_name("motor")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
