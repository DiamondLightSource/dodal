import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import assert_reading, get_mock_put, partial_reading

from dodal.devices.enum_device import EnumDevice


class EnumForDevice(StrictEnum):
    OPTION_1 = "Option1"
    OPTION_2 = "Option2"


@pytest.fixture
def enum_device(RE: RunEngine) -> EnumDevice[EnumForDevice]:
    with init_devices(mock=True):
        enum_device = EnumDevice[EnumForDevice]("TEST:", EnumForDevice)
    return enum_device


async def test_enum_device_read(enum_device: EnumDevice[EnumForDevice]) -> None:
    await assert_reading(
        enum_device, {enum_device.state.name: partial_reading(EnumForDevice.OPTION_1)}
    )


def test_enum_device_set(enum_device: EnumDevice[EnumForDevice], RE: RunEngine) -> None:
    value = EnumForDevice.OPTION_2
    RE(bps.mv(enum_device, value))
    get_mock_put(enum_device.state).assert_awaited_once_with(value, wait=True)
