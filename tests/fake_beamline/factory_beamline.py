from unittest.mock import AsyncMock, MagicMock

import ophyd
from bluesky.protocols import Readable, Reading, SyncOrAsync
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import Device

from dodal.common.beamlines.beamline_utils import device_factory, device_instantiation
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
def mock_device(**kwargs) -> ReadableDevice:
    device = MagicMock()
    device.name = "mock_device"
    device.connect = AsyncMock()
    device.my_kwargs = kwargs
    return device  # type: ignore


@device_factory(skip=True)
def ophyd_v1_device(mock: bool = False, **kwargs) -> ophyd.Device:
    device = device_instantiation(
        ophyd.Device, "my_v1_device", "my_prefix", False, mock
    )
    device.wait_for_connection = MagicMock()
    device.my_kwargs = kwargs
    return device
