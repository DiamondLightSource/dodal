import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.current_amplifiers import CountMode, StruckScaler
from dodal.devices.scaler_card import ScalerCardController


@pytest.fixture
async def struck_scaler() -> StruckScaler:
    async with init_devices(mock=True):
        struck_scaler = StruckScaler(prefix="BLXX-EA-SCLR-01", suffix=".S17")
    return struck_scaler


def test_struck_scaler_is_a_scaler_card_controller(struck_scaler: StruckScaler):
    assert isinstance(struck_scaler, ScalerCardController)


def test_struck_scaler_pv_names(struck_scaler: StruckScaler):
    assert struck_scaler.count.source.endswith("BLXX-EA-SCLR-01.S17")
    assert struck_scaler.start_count.source.endswith("BLXX-EA-SCLR-01.CNT")
    assert struck_scaler.integration_time.source.endswith("BLXX-EA-SCLR-01.TP")
    assert struck_scaler.mode.source.endswith("BLXX-EA-SCLR-01:AutoCount")


async def test_struck_scaler_read_and_configuration(struck_scaler: StruckScaler):
    await assert_reading(struck_scaler, {"struck_scaler-count": partial_reading(0.0)})
    await assert_configuration(
        struck_scaler,
        {
            "struck_scaler-integration_time": partial_reading(0.0),
            "struck_scaler-mode": partial_reading(CountMode.AUTO),
        },
    )


async def test_struck_scaler_set_sets_integration_time(
    struck_scaler: StruckScaler,
):
    await struck_scaler.set(2.5)
    get_mock_put(struck_scaler.integration_time).assert_awaited_once_with(2.5)


async def test_struck_scaler_stage_and_unstage_set_count_mode(
    struck_scaler: StruckScaler,
):
    await struck_scaler.stage()
    assert await struck_scaler.mode.get_value() == CountMode.ONE_SHOT
    await struck_scaler.unstage()
    assert await struck_scaler.mode.get_value() == CountMode.AUTO


async def test_struck_scaler_trigger_completes_in_mock_mode(
    struck_scaler: StruckScaler,
):
    await struck_scaler.trigger()
    get_mock_put(struck_scaler.start_count).assert_awaited_once_with(True)
    assert await struck_scaler.start_count.get_value() is False


async def test_struck_scaler_voltage_uses_integration_time(
    struck_scaler: StruckScaler,
):
    set_mock_value(struck_scaler.count, 4e5)
    set_mock_value(struck_scaler.integration_time, 2.0)
    assert await struck_scaler.count_per_sec.get_value() == 2e5
    assert await struck_scaler.voltage.get_value() == 2.0
