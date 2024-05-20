from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor
from ophyd.utils import DisconnectedError

from dodal.devices.cryostream import Cryo


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> EpicsMotor:
    raise DisconnectedError


def device_c() -> Cryo:
    return _mock_with_name("cryo")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
