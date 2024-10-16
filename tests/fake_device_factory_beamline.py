from unittest.mock import MagicMock

from bluesky.protocols import Readable
from ophyd_async.core import Device

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.cryostream import CryoStream


class ReadableDevice(Readable, Device): ...


@device_factory(skip=True, eager_connect=False)
def device_a() -> ReadableDevice:
    return _mock_with_name("readable")


@device_factory(skip=lambda: True, eager_connect=False)
def device_c() -> CryoStream:
    return _mock_with_name("cryo")


def _mock_with_name(name: str) -> MagicMock:
    mock = MagicMock()
    mock.name = name
    return mock
