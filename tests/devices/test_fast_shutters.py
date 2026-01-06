import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.fast_shutter import GenericFastShutter


class ShutterStates(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"


@pytest.fixture
def shutter() -> GenericFastShutter[ShutterStates]:
    with init_devices(mock=True):
        shutter = GenericFastShutter[ShutterStates](
            "TEST:",
            ShutterStates.OPEN,
            ShutterStates.CLOSE,
        )
    return shutter


async def test_shutter_set_open_close_without_knowing_enum_values(
    shutter: GenericFastShutter, run_engine: RunEngine
) -> None:
    run_engine(bps.mv(shutter, shutter.open_state))
    assert await shutter.state.get_value() == ShutterStates.OPEN
    run_engine(bps.mv(shutter, shutter.close_state))
    assert await shutter.state.get_value() == ShutterStates.CLOSE


async def test_shutter_is_open(
    shutter: GenericFastShutter, run_engine: RunEngine
) -> None:
    run_engine(bps.mv(shutter, shutter.open_state))
    assert await shutter.is_open()
    assert not await shutter.is_closed()


async def test_shutter_is_closed(
    shutter: GenericFastShutter, run_engine: RunEngine
) -> None:
    run_engine(bps.mv(shutter, shutter.close_state))
    assert not await shutter.is_open()
    assert await shutter.is_closed()
