import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import set_mock_value

from dodal.devices.hutch_shutter import (
    HutchNotInterlockedError,
    HutchShutter,
    ShutterDemand,
)


@pytest.fixture
async def fake_shutter() -> HutchShutter:
    RunEngine()
    shutter = HutchShutter("", name="fake_shutter")
    await shutter.connect(mock=True)

    return shutter


def test_shutter_is_created(fake_shutter: HutchShutter):
    assert isinstance(fake_shutter, HutchShutter)


async def test_shutter_raises_error_on_set_if_hutch_not_interlocked(
    fake_shutter: HutchShutter,
):
    set_mock_value(fake_shutter.interlock.status, 1)
    assert await fake_shutter.interlock.is_insterlocked() is False

    with pytest.raises(HutchNotInterlockedError):
        await fake_shutter.set(ShutterDemand.CLOSE)
