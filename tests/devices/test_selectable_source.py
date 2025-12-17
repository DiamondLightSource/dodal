import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.selectable_source import SelectedSource, SourceSelector


@pytest.fixture
async def source_selector() -> SourceSelector:
    with init_devices(mock=True):
        source_selector = SourceSelector()
    return source_selector


async def test_source_selector_read(source_selector: SourceSelector) -> None:
    await assert_reading(
        source_selector,
        {
            f"{source_selector.name}-selected_source": partial_reading(
                SelectedSource.SOURCE1
            )
        },
    )
