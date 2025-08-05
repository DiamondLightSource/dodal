from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor

from dodal.devices.cryostream import CryoStream
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.utils import OphydV2Device


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> Motor:
    return _mock_with_name("motor")


def device_c() -> CryoStream:
    return _mock_with_name("cryo")


def generic_device_d() -> DiamondFilter[I03Filters]:
    return _mock_with_name("diamond_filter")


def plain_ophyd_v2_device() -> OphydV2Device:
    return _mock_with_name("ophyd_v2_device")


def not_device() -> int:
    return 5


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
