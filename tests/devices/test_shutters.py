import pytest
from bluesky import FailedStatus, RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.shutters import GenericShutter


class ShutterStates(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"
    FAULT = "Fault"


@pytest.fixture
def shutter(RE: RunEngine) -> GenericShutter[ShutterStates]:
    with init_devices(mock=True):
        shutter = GenericShutter[ShutterStates](
            "TEST:",
            ShutterStates.OPEN,
            ShutterStates.CLOSE,
        )
    return shutter


async def test_shutter_set_open_close_without_knowing_enum_values(
    shutter: GenericShutter, RE: RunEngine
) -> None:
    RE(bps.mv(shutter, shutter.OPEN))
    assert await shutter.state.get_value() == ShutterStates.OPEN
    RE(bps.mv(shutter, shutter.CLOSE))
    assert await shutter.state.get_value() == ShutterStates.CLOSE


def test_shutter_invalid_set(shutter: GenericShutter, RE: RunEngine) -> None:
    with pytest.raises(FailedStatus):
        RE(bps.mv(shutter, ShutterStates.FAULT))


async def test_shutter_is_open(shutter: GenericShutter, RE: RunEngine) -> None:
    RE(bps.mv(shutter, shutter.OPEN))
    assert await shutter.is_open()
    assert not await shutter.is_closed()


async def test_shutter_is_closed(shutter: GenericShutter, RE: RunEngine) -> None:
    RE(bps.mv(shutter, shutter.CLOSE))
    assert not await shutter.is_open()
    assert await shutter.is_closed()
