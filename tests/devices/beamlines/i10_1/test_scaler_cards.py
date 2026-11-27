import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i10_1 import I10JScalerChannels
from dodal.devices.scaler_card import CountMode, ScalerCard, Struck32ChannelScaler


@pytest.fixture
async def scaler_controller() -> Struck32ChannelScaler:
    async with init_devices(mock=True):
        scaler_controller = Struck32ChannelScaler(
            prefix="BLXX-EA-DET-007:",
            stage_mode=CountMode.ONE_SHOT,
            unstage_mode=CountMode.AUTO,
        )
    return scaler_controller


@pytest.fixture
async def scaler_card(
    scaler_controller: Struck32ChannelScaler,
) -> ScalerCard[I10JScalerChannels]:
    async with init_devices(mock=True):
        scaler_card = ScalerCard(
            channels=I10JScalerChannels(scaler_controller),
            controller=scaler_controller,
        )
    return scaler_card


async def test_i10j_scaler_card_read(scaler_card: ScalerCard[I10JScalerChannels]):
    await assert_reading(
        scaler_card,
        {
            "scaler_card-channel-mon-count": partial_reading(0.0),
            "scaler_card-channel-tey-count": partial_reading(0.0),
            "scaler_card-channel-fy-count": partial_reading(0.0),
            "scaler_card-channel-fy2-count": partial_reading(0.0),
        },
    )
    await assert_configuration(
        scaler_card, {"scaler_controller-integration_time": partial_reading(0.0)}
    )


async def test_i10j_scaler_controller_reads_all_channels(
    scaler_controller: Struck32ChannelScaler,
    scaler_card: ScalerCard[I10JScalerChannels],
):
    set_mock_value(scaler_card.channel.tey.count, 3.0)
    await assert_reading(
        scaler_controller,
        {
            "scaler_card-channel-mon-count": partial_reading(0.0),
            "scaler_card-channel-tey-count": partial_reading(3.0),
            "scaler_card-channel-fy-count": partial_reading(0.0),
            "scaler_card-channel-fy2-count": partial_reading(0.0),
        },
    )


def test_i10j_scaler_channels_share_one_controller(
    scaler_controller: Struck32ChannelScaler,
    scaler_card: ScalerCard[I10JScalerChannels],
):
    channels = scaler_card.channel
    for channel in [channels.mon, channels.tey, channels.fy, channels.fy2]:
        assert channel.controller is scaler_controller


async def test_i10j_scaler_card_stage_sets_controller_mode(
    scaler_controller: Struck32ChannelScaler,
    scaler_card: ScalerCard[I10JScalerChannels],
):
    await scaler_card.stage()
    assert await scaler_controller.mode.get_value() == CountMode.ONE_SHOT
    await scaler_card.unstage()
    assert await scaler_controller.mode.get_value() == CountMode.AUTO
