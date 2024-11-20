from unittest.mock import AsyncMock, MagicMock

from bluesky.protocols import Readable, Reading, SyncOrAsync
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import Device

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.cryostream import CryoStream


class ReadableDevice(Readable, Device):
    def read(self) -> SyncOrAsync[dict[str, Reading]]:
        return {}

    def describe(self) -> SyncOrAsync[dict[str, DataKey]]:
        return {}


@device_factory(skip=True)
def device_a() -> ReadableDevice:
    return ReadableDevice("readable")


@device_factory(skip=lambda: True)
def device_c() -> CryoStream:
    return CryoStream("FOO:")


@device_factory(skip=True)
def mock_device() -> ReadableDevice:
    device = MagicMock()
    device.name = "mock_device"
    device.connect = AsyncMock()
    return device  # type: ignore
