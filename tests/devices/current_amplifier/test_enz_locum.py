import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.current_amplifiers import (
    EnzLocum,
    EnzLocumBiasSource,
    EnzLocumBiasSourceReadback,
    EnzLocumIntegrationWindow,
    EnzLocumRange,
    EnzLocumRangeReadback,
)


@pytest.fixture
async def locum() -> EnzLocum:
    async with init_devices(mock=True):
        locum = EnzLocum("LOCUM:")
    return locum


def test_locum_uses_prefix_for_pvs(locum: EnzLocum) -> None:
    assert locum.range.source == "mock+ca://LOCUM:SETRANGE"
    assert locum.range_readback.source == "mock+ca://LOCUM:MRREADBACK"
    assert locum.range_max.source == "mock+ca://LOCUM:RANGEMAX"
    assert locum.autorange.source == "mock+ca://LOCUM:AUTO"
    assert locum.bias_source.source == "mock+ca://LOCUM:SETBIASV"
    assert locum.bias_source_readback.source == "mock+ca://LOCUM:BIASV"
    assert locum.integration_window.source == "mock+ca://LOCUM:SETWINDOW"
    assert locum.integration_window_readback.source == "mock+ca://LOCUM:WINDOW"


async def test_locum_set_range(locum: EnzLocum) -> None:
    await locum.range.set(EnzLocumRange.RANGE_10NA)
    assert await locum.range.get_value() == EnzLocumRange.RANGE_10NA


async def test_locum_configuration(locum: EnzLocum) -> None:
    set_mock_value(locum.range, EnzLocumRange.AUTO)
    set_mock_value(locum.range_readback, EnzLocumRangeReadback.RANGE_1UA)
    set_mock_value(locum.range_max, 1e-6)
    set_mock_value(locum.autorange, True)
    set_mock_value(locum.bias_source, EnzLocumBiasSource.GROUND)
    set_mock_value(locum.bias_source_readback, EnzLocumBiasSourceReadback.GROUND)
    set_mock_value(locum.integration_window, EnzLocumIntegrationWindow.WINDOW_16)
    set_mock_value(
        locum.integration_window_readback, EnzLocumIntegrationWindow.WINDOW_16
    )

    await assert_configuration(
        locum,
        {
            "locum-range": partial_reading(EnzLocumRange.AUTO),
            "locum-range_readback": partial_reading(EnzLocumRangeReadback.RANGE_1UA),
            "locum-range_max": partial_reading(1e-6),
            "locum-autorange": partial_reading(True),
            "locum-bias_source": partial_reading(EnzLocumBiasSource.GROUND),
            "locum-bias_source_readback": partial_reading(
                EnzLocumBiasSourceReadback.GROUND
            ),
            "locum-integration_window": partial_reading(
                EnzLocumIntegrationWindow.WINDOW_16
            ),
            "locum-integration_window_readback": partial_reading(
                EnzLocumIntegrationWindow.WINDOW_16
            ),
        },
    )
