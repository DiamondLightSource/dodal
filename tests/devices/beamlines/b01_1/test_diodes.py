import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.b01_1.diodes import RGBDiodes
from dodal.devices.current_amplifiers import (
    EnzLocumBiasSource,
    EnzLocumBiasSourceReadback,
    EnzLocumIntegrationWindow,
    EnzLocumRange,
    EnzLocumRangeReadback,
)


@pytest.fixture
async def diodes() -> RGBDiodes:
    async with init_devices(mock=True):
        diodes = RGBDiodes("PANDA:FmcIn:Val", "LOCUM:", green_channel=4)
    return diodes


def test_diodes_use_pvs_for_their_channel(diodes: RGBDiodes) -> None:
    assert diodes.red.source == "mock+ca://PANDA:FmcIn:Val5"
    assert diodes.green.source == "mock+ca://PANDA:FmcIn:Val4"
    assert diodes.blue.source == "mock+ca://PANDA:FmcIn:Val7"
    assert diodes.amplifier.range.source == "mock+ca://LOCUM:SETRANGE"


async def test_diodes_read_values(diodes: RGBDiodes) -> None:
    set_mock_value(diodes.red, 1)
    set_mock_value(diodes.green, 2)
    set_mock_value(diodes.blue, 3)

    await assert_reading(
        diodes,
        {
            "diodes-red": partial_reading(1),
            "diodes-green": partial_reading(2),
            "diodes-blue": partial_reading(3),
        },
    )


async def test_diodes_configuration_has_amplifier_settings(
    diodes: RGBDiodes,
) -> None:
    amplifier = diodes.amplifier
    set_mock_value(amplifier.range, EnzLocumRange.AUTO)
    set_mock_value(amplifier.range_readback, EnzLocumRangeReadback.RANGE_1UA)
    set_mock_value(amplifier.range_max, 1e-6)
    set_mock_value(amplifier.autorange, True)
    set_mock_value(amplifier.bias_source, EnzLocumBiasSource.GROUND)
    set_mock_value(amplifier.bias_source_readback, EnzLocumBiasSourceReadback.GROUND)
    set_mock_value(amplifier.integration_window, EnzLocumIntegrationWindow.WINDOW_16)
    set_mock_value(
        amplifier.integration_window_readback, EnzLocumIntegrationWindow.WINDOW_16
    )

    await assert_configuration(
        diodes,
        {
            "diodes-amplifier-range": partial_reading(EnzLocumRange.AUTO),
            "diodes-amplifier-range_readback": partial_reading(
                EnzLocumRangeReadback.RANGE_1UA
            ),
            "diodes-amplifier-range_max": partial_reading(1e-6),
            "diodes-amplifier-autorange": partial_reading(True),
            "diodes-amplifier-bias_source": partial_reading(EnzLocumBiasSource.GROUND),
            "diodes-amplifier-bias_source_readback": partial_reading(
                EnzLocumBiasSourceReadback.GROUND
            ),
            "diodes-amplifier-integration_window": partial_reading(
                EnzLocumIntegrationWindow.WINDOW_16
            ),
            "diodes-amplifier-integration_window_readback": partial_reading(
                EnzLocumIntegrationWindow.WINDOW_16
            ),
        },
    )
