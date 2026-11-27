import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.current_amplifiers import StruckScalerChannel
from dodal.devices.scaler_card import (
    CountMode,
    ScalerCardController,
    Struck32ChannelScaler,
)


@pytest.fixture
async def struck_scaler() -> Struck32ChannelScaler:
    async with init_devices(mock=True):
        struck_scaler = Struck32ChannelScaler(
            prefix="BLXX-EA-SCLR-01",
            stage_mode=CountMode.ONE_SHOT,
            unstage_mode=CountMode.AUTO,
        )
    return struck_scaler


@pytest.fixture
async def channel_1(struck_scaler: Struck32ChannelScaler) -> StruckScalerChannel:
    async with init_devices(mock=True):
        channel_1 = StruckScalerChannel(struck_scaler, suffix=".S17")
    return channel_1


@pytest.fixture
async def channel_2(struck_scaler: Struck32ChannelScaler) -> StruckScalerChannel:
    async with init_devices(mock=True):
        channel_2 = StruckScalerChannel(struck_scaler, suffix=".S18")
    return channel_2


def test_struck_scaler_is_a_scaler_card_controller(
    struck_scaler: Struck32ChannelScaler,
):
    assert isinstance(struck_scaler, ScalerCardController)


def test_struck_scaler_pv_names(
    struck_scaler: Struck32ChannelScaler, channel_1: StruckScalerChannel
):
    assert struck_scaler.start_count.source.endswith("BLXX-EA-SCLR-01.CNT")
    assert struck_scaler.integration_time.source.endswith("BLXX-EA-SCLR-01.TP")
    assert struck_scaler.mode.source.endswith("BLXX-EA-SCLR-01:AutoCount")
    assert struck_scaler.delay_time.source.endswith("BLXX-EA-SCLR-01.DLY")
    assert channel_1.count.source.endswith("BLXX-EA-SCLR-01.S17")


def test_channels_share_the_card_controller(
    struck_scaler: Struck32ChannelScaler,
    channel_1: StruckScalerChannel,
    channel_2: StruckScalerChannel,
):
    assert channel_1.controller is struck_scaler
    assert channel_2.controller is struck_scaler


async def test_struck_scaler_configuration(struck_scaler: Struck32ChannelScaler):
    await assert_configuration(
        struck_scaler,
        {
            "struck_scaler-integration_time": partial_reading(0.0),
            "struck_scaler-mode": partial_reading(CountMode.AUTO),
            "struck_scaler-delay_time": partial_reading(0.0),
        },
    )


async def test_channel_does_not_register_itself_on_controller(
    struck_scaler: Struck32ChannelScaler, channel_1: StruckScalerChannel
):
    await assert_reading(struck_scaler, {})


async def test_channel_read_and_configuration(channel_1: StruckScalerChannel):
    await assert_reading(channel_1, {"channel_1-count": partial_reading(0.0)})
    await assert_configuration(channel_1, {})


async def test_channel_set_sets_shared_integration_time(
    struck_scaler: Struck32ChannelScaler,
    channel_1: StruckScalerChannel,
    channel_2: StruckScalerChannel,
):
    await channel_1.set(2.5)
    get_mock_put(struck_scaler.integration_time).assert_awaited_once_with(2.5)
    assert await channel_2.controller.integration_time.get_value() == 2.5


async def test_channel_trigger_starts_a_single_card_count(
    struck_scaler: Struck32ChannelScaler, channel_1: StruckScalerChannel
):
    await channel_1.trigger()
    get_mock_put(struck_scaler.start_count).assert_awaited_once_with(True)
    assert await struck_scaler.start_count.get_value() is False


async def test_channel_stage_and_unstage_do_not_change_card_mode(
    struck_scaler: Struck32ChannelScaler, channel_1: StruckScalerChannel
):
    await channel_1.stage()
    await channel_1.unstage()
    get_mock_put(struck_scaler.mode).assert_not_called()


async def test_struck_scaler_stage_and_unstage_set_configured_modes(
    struck_scaler: Struck32ChannelScaler,
):
    await struck_scaler.stage()
    assert await struck_scaler.mode.get_value() == CountMode.ONE_SHOT
    await struck_scaler.unstage()
    assert await struck_scaler.mode.get_value() == CountMode.AUTO


async def test_channel_voltage_uses_card_integration_time(
    struck_scaler: Struck32ChannelScaler, channel_1: StruckScalerChannel
):
    set_mock_value(channel_1.count, 4e5)
    set_mock_value(struck_scaler.integration_time, 2.0)
    assert await channel_1.count_per_sec.get_value() == 2e5
    assert await channel_1.voltage.get_value() == 2.0
