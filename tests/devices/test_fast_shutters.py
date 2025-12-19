import asyncio

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import InOut, OnOff, init_devices
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.selectable_source import SelectedSource, SourceSelector


@pytest.fixture
def shutter1() -> GenericFastShutter[InOut]:
    with init_devices(mock=True):
        shutter1 = GenericFastShutter[InOut](
            pv="TEST:",
            open_state=InOut.OUT,
            close_state=InOut.IN,
        )
    return shutter1


async def test_shutter_set_open_close_without_knowing_enum_values(
    shutter1: GenericFastShutter, run_engine: RunEngine
) -> None:
    run_engine(bps.mv(shutter1, shutter1.open_state), wait=True)
    assert await shutter1.shutter_state.get_value() == InOut.OUT
    run_engine(bps.mv(shutter1, shutter1.close_state), wait=True)
    assert await shutter1.shutter_state.get_value() == InOut.IN


async def test_shutter_read(shutter1: GenericFastShutter) -> None:
    await assert_reading(
        shutter1, {f"{shutter1.name}-shutter_state": partial_reading(InOut.IN)}
    )


@pytest.fixture
def shutter2() -> GenericFastShutter[InOut]:
    with init_devices(mock=True):
        shutter2 = GenericFastShutter[InOut](
            pv="TEST:",
            open_state=InOut.OUT,
            close_state=InOut.IN,
        )
    return shutter2


@pytest.fixture
def source_selector() -> SourceSelector:
    with init_devices(mock=True):
        source_selector = SourceSelector()
    return source_selector


@pytest.fixture
def dual_fast_shutter(
    shutter1: GenericFastShutter[InOut],
    shutter2: GenericFastShutter[InOut],
    source_selector: SourceSelector,
) -> DualFastShutter[InOut]:
    with init_devices(mock=True):
        dual_fast_shutter = DualFastShutter[InOut](
            shutter1,
            shutter2,
            source_selector.selected_source,
        )
    return dual_fast_shutter


async def test_dual_fast_shutter_read_shutter_state(
    shutter1: GenericFastShutter,
    shutter2: GenericFastShutter,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
    run_engine: RunEngine,
) -> None:
    # Setup test so that the two shutters are not in the same state so test can tell
    # them a part.
    run_engine(bps.mv(shutter1, shutter1.open_state))
    run_engine(bps.mv(shutter2, shutter2.close_state))

    run_engine(bps.mv(source_selector, SelectedSource.SOURCE2))
    assert await dual_fast_shutter.shutter_state.get_value() == shutter2.close_state

    run_engine(bps.mv(source_selector, SelectedSource.SOURCE1))
    assert await dual_fast_shutter.shutter_state.get_value() == shutter1.open_state


async def test_dual_fast_shutter_set_shutter_state(
    shutter1: GenericFastShutter,
    shutter2: GenericFastShutter,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(source_selector, SelectedSource.SOURCE2))

    run_engine(bps.mv(dual_fast_shutter, dual_fast_shutter.open_state))
    assert await shutter2.shutter_state.get_value() == shutter2.open_state
    assert await shutter1.shutter_state.get_value() == shutter1.close_state

    run_engine(bps.mv(dual_fast_shutter, dual_fast_shutter.close_state))
    assert await shutter2.shutter_state.get_value() == shutter2.close_state
    assert await shutter1.shutter_state.get_value() == shutter1.close_state

    run_engine(bps.mv(source_selector, SelectedSource.SOURCE1))

    run_engine(bps.mv(dual_fast_shutter, dual_fast_shutter.open_state))
    assert await shutter1.shutter_state.get_value() == shutter1.open_state
    assert await shutter2.shutter_state.get_value() == shutter2.close_state

    run_engine(bps.mv(dual_fast_shutter, dual_fast_shutter.close_state))
    assert await shutter1.shutter_state.get_value() == shutter1.close_state
    assert await shutter2.shutter_state.get_value() == shutter2.close_state


def test_dual_fast_shutter_open_close_states_are_correct(
    shutter1: GenericFastShutter,
    shutter2: GenericFastShutter,
    dual_fast_shutter: DualFastShutter,
) -> None:
    assert dual_fast_shutter.open_state == shutter1.open_state
    assert dual_fast_shutter.open_state == shutter2.open_state

    assert dual_fast_shutter.close_state == shutter1.close_state
    assert dual_fast_shutter.close_state == shutter2.close_state


async def test_dual_fast_shutter_read(
    dual_fast_shutter: DualFastShutter,
    shutter1: GenericFastShutter,
    shutter2: GenericFastShutter,
    source_selector: SourceSelector,
) -> None:
    shutter1_read, shutter2_read, source_selector_read = await asyncio.gather(
        shutter1.read(), shutter2.read(), source_selector.read()
    )
    await assert_reading(
        dual_fast_shutter,
        {f"{dual_fast_shutter.name}-shutter_state": partial_reading(InOut.IN)}
        | shutter1_read
        | shutter2_read
        | source_selector_read,
    )


async def test_dual_fast_shutter_read_configuration(
    dual_fast_shutter: DualFastShutter,
    shutter1: GenericFastShutter,
    shutter2: GenericFastShutter,
) -> None:
    await assert_configuration(
        dual_fast_shutter,
        {
            f"{dual_fast_shutter.name}-shutter1_device_name": partial_reading(
                shutter1.name
            ),
            f"{dual_fast_shutter.name}-shutter2_device_name": partial_reading(
                shutter2.name
            ),
        },
    )


async def test_dual_fast_shutter_raises_error_if_shutters_have_different_open_close_states(
    shutter1: GenericFastShutter,
    source_selector: SourceSelector,
) -> None:
    with init_devices(mock=True):
        other_shutter = GenericFastShutter(
            pv="TEST:", open_state=OnOff.ON, close_state=OnOff.OFF
        )

    with pytest.raises(
        ValueError,
        match=f"{shutter1.open_state} is not same value as {other_shutter.open_state}",
    ):
        with init_devices(mock=True):
            DualFastShutter(shutter1, other_shutter, source_selector.selected_source)
