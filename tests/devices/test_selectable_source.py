import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.selectable_source import (
    SelectedSource,
    SourceSelector,
    get_obj_from_selected_source,
)


@pytest.fixture
async def source_selector() -> SourceSelector:
    with init_devices(mock=True):
        source_selector = SourceSelector()
    return source_selector


async def test_source_selector_set(
    run_engine: RunEngine, source_selector: SourceSelector
) -> None:
    run_engine(bps.mv(source_selector, SelectedSource.SOURCE2))
    assert await source_selector.selected_source.get_value() == SelectedSource.SOURCE2


async def test_source_selector_read(source_selector: SourceSelector) -> None:
    await assert_reading(
        source_selector,
        {
            f"{source_selector.name}-selected_source": partial_reading(
                SelectedSource.SOURCE1
            )
        },
    )


def test_get_obj_from_selected_source() -> None:
    obj1, obj2 = 1, 2
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE1, obj1, obj2)
    assert selected_obj is obj1
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE2, obj1, obj2)
    assert selected_obj is obj2
