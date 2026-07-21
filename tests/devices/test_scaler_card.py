from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import (
    DeviceVector,
    StandardReadable,
    get_mock_put,
    init_devices,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.scaler_card import ScalerCardChannels, ScalerCardController


@pytest.fixture
def scaler_controller() -> ScalerCardController:
    with init_devices(mock=True):
        scaler_controller = ScalerCardController("TEST:", "CNT", "VAL")
    return scaler_controller


@pytest.fixture
def scaler1(scaler_controller: ScalerCardController):
    """Single channel example."""
    with init_devices(mock=True):
        scaler1 = ScalerCardChannels(
            channels=soft_signal_rw(float), controller=scaler_controller
        )
    return scaler1


@pytest.fixture
def scaler2(scaler_controller: ScalerCardController):
    """Multi channel example with device vector."""
    with init_devices(mock=True):
        scaler2 = ScalerCardChannels(
            channels=DeviceVector(
                {
                    0: epics_signal_r(float, "TEST1:"),
                    1: epics_signal_r(float, "TEST2:"),
                    2: epics_signal_r(float, "TEST3:"),
                }
            ),
            controller=scaler_controller,
        )
    return scaler2


class MultiChannelExample(StandardReadable):
    def __init__(self, name: str = ""):
        with self.add_children_as_readables():
            self.hm3amp20 = soft_signal_rw(float)
            self.sm5amp8 = soft_signal_rw(float)
        super().__init__(name)


@pytest.fixture
def scaler3(scaler_controller: ScalerCardController):
    """Multi channel example with sub devices."""
    with init_devices(mock=True):
        scaler2 = ScalerCardChannels(
            channels=MultiChannelExample(),
            controller=scaler_controller,
        )
    return scaler2


async def test_scaler1_single_channel_read(
    scaler1: ScalerCardChannels,
) -> None:
    await assert_reading(scaler1, {"scaler1-channel": partial_reading(0)})


async def test_scaler2_multi_channel_read(
    scaler2: ScalerCardChannels,
) -> None:
    await assert_reading(
        scaler2,
        {
            "scaler2-channel-0": partial_reading(0),
            "scaler2-channel-1": partial_reading(0),
            "scaler2-channel-2": partial_reading(0),
        },
    )


async def test_scaler3_multi_channel_read(
    scaler3: ScalerCardChannels,
) -> None:
    await assert_reading(
        scaler3,
        {
            "scaler2-channel-hm3amp20": partial_reading(0),
            "scaler2-channel-sm5amp8": partial_reading(0),
        },
    )


async def test_scaler_controller_read_configuration(
    scaler_controller: ScalerCardController,
) -> None:
    await assert_configuration(
        scaler_controller, {"scaler_controller-integration_time": partial_reading(0.0)}
    )


async def test_scaler_controller_set(scaler_controller: ScalerCardController) -> None:
    value = 1
    await scaler_controller.set(value)
    get_mock_put(scaler_controller.integration_time).assert_awaited_once_with(value)


async def test_scaler_card_channels_set_calls_controller_set(
    scaler1: ScalerCardChannels,
):
    set_mock = AsyncMock()
    scaler1.controller_ref().set = set_mock

    await scaler1.set(2)
    set_mock.assert_called_once_with(2)


async def test_scaler_card_channels_trigger_calls_controller_trigger(
    scaler1: ScalerCardChannels,
):
    trigger_mock = AsyncMock()
    scaler1.controller_ref().trigger = trigger_mock

    await scaler1.trigger()
    trigger_mock.assert_called_once()


async def test_scaler_controller_trigger_sets_counting_true_then_false(
    scaler_controller: ScalerCardController,
) -> None:
    values = []
    scaler_controller.start_count.subscribe(values.append)
    await scaler_controller.trigger()
    scaler_controller.start_count.clear_sub(values.append)

    states = []
    expected_states = [False, True, False]
    for v in values:
        states.append(v[scaler_controller.start_count.name]["value"])
    assert states == expected_states


async def test_scaler_controller_multiple_connects_has_one_subscribe(
    scaler_controller: ScalerCardController,
) -> None:
    expected_subscribers = 1
    number_of_subscribers = len(scaler_controller.start_count._get_cache()._listeners)
    assert number_of_subscribers == expected_subscribers
    # Test if we connect again if another subscriber is added, checking for memory leaks.
    for _ in range(3):
        await scaler_controller.connect(mock=True)
        assert (
            len(scaler_controller.start_count._get_cache()._listeners)
            == expected_subscribers
        )

    def dummy(value):
        pass

    # Now subscribe to make sure it does go up and not checking the wrong thing.
    scaler_controller.start_count.subscribe(dummy)
    assert len(scaler_controller.start_count._get_cache()._listeners) == 2
