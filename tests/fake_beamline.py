from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.devices.cryostream import CryoStream
from dodal.devices.diamond_filter import DiamondFilter, I03Filters


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> EpicsMotor:
    return _mock_with_name("motor")


def device_c() -> CryoStream:
    return _mock_with_name("cryo")


def generic_device_d() -> DiamondFilter[I03Filters]:
    return _mock_with_name("diamond_filter")


def not_device() -> int:
    return 5


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
