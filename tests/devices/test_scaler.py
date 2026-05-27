import time
from unittest.mock import AsyncMock, call

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.scaler import ScalerController, SimpleChannelScaler


@pytest.fixture
def scaler1() -> ScalerController:
    with init_devices(mock=True):
        scaler1 = ScalerController("TEST:")
    return scaler1


@pytest.fixture
def hm3amp20_1(scaler1: ScalerController) -> SimpleChannelScaler:
    with init_devices(mock=True):
        hm3amp20_1 = SimpleChannelScaler(scaler1, 1)
    return hm3amp20_1


@pytest.fixture
def sm5amp8_1(scaler1: ScalerController) -> SimpleChannelScaler:
    with init_devices(mock=True):
        sm5amp8_1 = SimpleChannelScaler(scaler1, 2)
    return sm5amp8_1


async def test_scaler_controller_read(scaler1: ScalerController) -> None:
    await assert_reading(scaler1, {})


async def test_scaler_controller_read_with_multiple_channels(
    scaler1: ScalerController,
    hm3amp20_1: SimpleChannelScaler,
    sm5amp8_1: SimpleChannelScaler,
) -> None:
    await assert_reading(
        scaler1,
        {
            "hm3amp20_1-count": partial_reading(0),
            "sm5amp8_1-count": partial_reading(0),
        },
    )


async def test_scaler_controller_read_configuration(scaler1: ScalerController) -> None:
    await assert_configuration(scaler1, {"scaler1-count_period": partial_reading(0.0)})


async def test_scaler_controller_trigger_waits_for_counting_to_finish(
    scaler1: ScalerController,
) -> None:
    start = time.monotonic()
    await scaler1.trigger()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.2
    assert await scaler1.counting.get_value() is False


async def test_scaler_controller_trigger_sets_counting_true_then_false(
    scaler1: ScalerController,
) -> None:
    values = []
    scaler1.counting.subscribe(values.append)
    await scaler1.trigger()

    states = []
    expected_states = [False, True, False]
    for v in values:
        states.append(v[scaler1.counting.name]["value"])
    assert states == expected_states


async def test_simple_channel_scaler_read(hm3amp20_1: SimpleChannelScaler) -> None:
    await assert_reading(
        hm3amp20_1,
        {
            "hm3amp20_1-count": partial_reading(0),
        },
    )


async def test_simple_channel_scaler_read_configuration(
    hm3amp20_1: SimpleChannelScaler,
) -> None:
    await assert_configuration(
        hm3amp20_1,
        {
            "scaler1-count_period": partial_reading(0),
        },
    )


async def test_simple_channel_scaler_trigger(
    scaler1: ScalerController, hm3amp20_1: SimpleChannelScaler, sm5amp8_1
) -> None:
    mock_trigger = AsyncMock()
    scaler1.trigger = mock_trigger

    await hm3amp20_1.trigger()
    mock_trigger.assert_awaited_once()

    await sm5amp8_1.trigger()
    mock_trigger.assert_has_calls([call(), call()])
