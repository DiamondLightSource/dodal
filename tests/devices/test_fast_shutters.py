import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.selectable_source import SourceSelector


class ShutterStates(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"


@pytest.fixture
def shutter1() -> GenericFastShutter[ShutterStates]:
    with init_devices(mock=True):
        shutter1 = GenericFastShutter[ShutterStates](
            "TEST:",
            ShutterStates.OPEN,
            ShutterStates.CLOSE,
        )
    return shutter1


async def test_shutter_set_open_close_without_knowing_enum_values(
    shutter1: GenericFastShutter, run_engine: RunEngine
) -> None:
    run_engine(bps.mv(shutter1, shutter1.open_state))
    assert await shutter1.shutter_state.get_value() == ShutterStates.OPEN
    run_engine(bps.mv(shutter1, shutter1.close_state))
    assert await shutter1.shutter_state.get_value() == ShutterStates.CLOSE


@pytest.fixture
def shutter2() -> GenericFastShutter[ShutterStates]:
    with init_devices(mock=True):
        shutter2 = GenericFastShutter[ShutterStates](
            "TEST:",
            ShutterStates.OPEN,
            ShutterStates.CLOSE,
        )
    return shutter2


@pytest.fixture
def source_selector() -> SourceSelector:
    return SourceSelector()


@pytest.fixture
def dual_fast_shutter(
    shutter1: GenericFastShutter[ShutterStates],
    shutter2: GenericFastShutter[ShutterStates],
    source_selector: SourceSelector,
) -> DualFastShutter[ShutterStates]:
    with init_devices(mock=True):
        dual_fast_shutter = DualFastShutter[ShutterStates](
            shutter1,
            shutter2,
            source_selector.selected_source,
        )
    return dual_fast_shutter


def test_dual_fast_shutter(dual_fast_shutter: DualFastShutter):
    pass
