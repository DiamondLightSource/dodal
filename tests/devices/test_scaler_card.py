import asyncio
from unittest.mock import AsyncMock

import pytest
from bluesky.protocols import Reading
from ophyd_async.core import (
    DeviceMap,
    DeviceVector,
    StandardReadable,
    get_mock_put,
    init_devices,
    set_mock_attr,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.scaler_card import (
    CountMode,
    Hytec8512Scaler,
    ScalerCard,
    ScalerCardController,
    ScanMode,
)


@pytest.fixture
def scaler_controller() -> ScalerCardController:
    with init_devices(mock=True):
        scaler_controller = ScalerCardController(
            "TEST:", "CNT", "VAL", "MODE", CountMode
        )
    return scaler_controller


@pytest.fixture
def scaler1(scaler_controller: ScalerCardController):
    """Single channel example."""
    with init_devices(mock=True):
        scaler1 = ScalerCard(
            channels=soft_signal_rw(float), controller=scaler_controller
        )
    return scaler1


@pytest.fixture
def scaler2(scaler_controller: ScalerCardController):
    """Multi channel example with device vector."""
    with init_devices(mock=True):
        scaler2 = ScalerCard(
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


@pytest.fixture
def scaler3(scaler_controller: ScalerCardController):
    """Multi channel example with device map."""
    with init_devices(mock=True):
        scaler3 = ScalerCard(
            channels=DeviceMap(
                {
                    "dev1": epics_signal_r(float, "TEST1:"),
                    "dev2": epics_signal_r(float, "TEST2:"),
                    "dev3": epics_signal_r(float, "TEST3:"),
                }
            ),
            controller=scaler_controller,
        )
    return scaler3


class MultiChannelExample(StandardReadable):
    def __init__(self, name: str = ""):
        with self.add_children_as_readables():
            self.hm3amp20 = soft_signal_rw(float)
            self.sm5amp8 = soft_signal_rw(float)
        super().__init__(name)


@pytest.fixture
def scaler4(scaler_controller: ScalerCardController):
    """Multi channel example with sub device."""
    with init_devices(mock=True):
        scaler4 = ScalerCard(
            channels=MultiChannelExample(),
            controller=scaler_controller,
        )
    return scaler4


async def test_scaler1_single_channel_read_and_configuration(
    scaler1: ScalerCard,
) -> None:
    await asyncio.gather(
        assert_reading(scaler1, {"scaler1-channel": partial_reading(0)}),
        assert_configuration(
            scaler1, {"scaler_controller-integration_time": partial_reading(0)}
        ),
    )


async def test_scaler2_multi_channel_device_vector_read_and_configuration(
    scaler2: ScalerCard,
) -> None:
    await asyncio.gather(
        assert_reading(
            scaler2,
            {
                "scaler2-channel-0": partial_reading(0),
                "scaler2-channel-1": partial_reading(0),
                "scaler2-channel-2": partial_reading(0),
            },
        ),
        assert_configuration(
            scaler2, {"scaler_controller-integration_time": partial_reading(0)}
        ),
    )


async def test_scaler3_multi_channel_device_map_read_and_configuration(
    scaler3: ScalerCard,
) -> None:
    await asyncio.gather(
        assert_reading(
            scaler3,
            {
                "scaler3-channel-dev1": partial_reading(0),
                "scaler3-channel-dev2": partial_reading(0),
                "scaler3-channel-dev3": partial_reading(0),
            },
        ),
        assert_configuration(
            scaler3, {"scaler_controller-integration_time": partial_reading(0)}
        ),
    )


async def test_scaler4_multi_channel_sub_device_read_and_configuration(
    scaler4: ScalerCard,
) -> None:
    await asyncio.gather(
        assert_reading(
            scaler4,
            {
                "scaler4-channel-hm3amp20": partial_reading(0),
                "scaler4-channel-sm5amp8": partial_reading(0),
            },
        ),
        assert_configuration(
            scaler4, {"scaler_controller-integration_time": partial_reading(0)}
        ),
    )


async def test_scaler_controller_read_configuration(
    scaler_controller: ScalerCardController,
) -> None:
    await assert_configuration(
        scaler_controller,
        {
            "scaler_controller-integration_time": partial_reading(0.0),
            "scaler_controller-count_mode": partial_reading(CountMode.AUTO),
        },
    )


async def test_scaler_controller_read_when_used_with_channel(
    scaler_controller: ScalerCardController, scaler1: ScalerCard
) -> None:
    await assert_reading(scaler_controller, {"scaler1-channel": partial_reading(0)})


async def test_scaler_controller_read_when_used_with_multiple_channels(
    scaler_controller: ScalerCardController,
    scaler1: ScalerCard,
    scaler2: ScalerCard,
    scaler3: ScalerCard,
    scaler4: ScalerCard,
) -> None:
    """Using multiple channels should add their readables to the master controller."""
    await assert_reading(
        scaler_controller,
        {
            "scaler1-channel": partial_reading(0),
            "scaler2-channel-0": partial_reading(0),
            "scaler2-channel-1": partial_reading(0),
            "scaler2-channel-2": partial_reading(0),
            "scaler3-channel-dev1": partial_reading(0),
            "scaler3-channel-dev2": partial_reading(0),
            "scaler3-channel-dev3": partial_reading(0),
            "scaler4-channel-hm3amp20": partial_reading(0),
            "scaler4-channel-sm5amp8": partial_reading(0),
        },
    )


async def test_scaler_controller_set(scaler_controller: ScalerCardController) -> None:
    value = 1
    await scaler_controller.set(value)
    get_mock_put(scaler_controller.integration_time).assert_awaited_once_with(value)


async def test_scaler_card_channels_set_calls_controller_set(
    scaler1: ScalerCard,
):
    set_mock = set_mock_attr(scaler1.controller_ref(), "set", AsyncMock())
    await scaler1.set(2)
    set_mock.assert_called_once_with(2)


async def test_scaler_card_channels_trigger_calls_controller_trigger(
    scaler1: ScalerCard,
):
    trigger_mock = set_mock_attr(scaler1.controller_ref(), "trigger", AsyncMock())
    await scaler1.trigger()
    trigger_mock.assert_called_once()


async def test_scaler_controller_trigger_sets_counting_true_then_false(
    scaler_controller: ScalerCardController,
) -> None:
    states = []
    expected_states = [False, True, False]

    def sub(readings: dict[str, Reading[bool]]):
        val = readings[scaler_controller.start_count.name]["value"]
        states.append(val)

    scaler_controller.start_count.subscribe(sub)
    await scaler_controller.trigger()
    scaler_controller.start_count.clear_sub(sub)

    assert states == expected_states


@pytest.fixture
def scaler_controller_with_stage_modes() -> ScalerCardController:
    with init_devices(mock=True):
        scaler_controller_with_stage_modes = ScalerCardController(
            "TEST:",
            "CNT",
            "VAL",
            "MODE",
            CountMode,
            stage_mode=CountMode.ONE_SHOT,
            unstage_mode=CountMode.AUTO,
        )
    return scaler_controller_with_stage_modes


def test_scaler_controller_count_mode_pv(
    scaler_controller: ScalerCardController,
) -> None:
    assert scaler_controller.count_mode.source.endswith("TEST:MODE")


async def test_scaler_controller_without_stage_modes_does_not_change_count_mode(
    scaler_controller: ScalerCardController,
) -> None:
    await scaler_controller.stage()
    await scaler_controller.unstage()
    get_mock_put(scaler_controller.count_mode).assert_not_called()


async def test_scaler_controller_sets_stage_and_unstage_modes(
    scaler_controller_with_stage_modes: ScalerCardController,
) -> None:
    controller = scaler_controller_with_stage_modes
    await controller.stage()
    assert await controller.count_mode.get_value() == CountMode.ONE_SHOT
    await controller.unstage()
    assert await controller.count_mode.get_value() == CountMode.AUTO


async def test_scaler_controller_only_unstage_mode_set() -> None:
    with init_devices(mock=True):
        controller = ScalerCardController(
            "TEST:", "CNT", "VAL", "MODE", CountMode, unstage_mode=CountMode.AUTO
        )
    await controller.stage()
    get_mock_put(controller.count_mode).assert_not_called()
    await controller.unstage()
    get_mock_put(controller.count_mode).assert_called_once_with(CountMode.AUTO)


@pytest.fixture
async def hytec_scaler() -> Hytec8512Scaler:
    async with init_devices(mock=True):
        hytec_scaler = Hytec8512Scaler("TEST:")
    return hytec_scaler


def test_hytec_scaler_pv_names(hytec_scaler: Hytec8512Scaler):
    assert hytec_scaler.start_count.source.endswith("TEST:STARTCOUNT")
    assert hytec_scaler.integration_time.source.endswith("TEST:PRESET")
    assert hytec_scaler.count_mode.source.endswith("TEST:Mode")


def test_hytec_scaler_has_no_delay_time(hytec_scaler: Hytec8512Scaler):
    assert not hasattr(hytec_scaler, "delay_time")


async def test_hytec_scaler_configuration(hytec_scaler: Hytec8512Scaler):
    await assert_configuration(
        hytec_scaler,
        {
            "hytec_scaler-integration_time": partial_reading(0.0),
            "hytec_scaler-count_mode": partial_reading(ScanMode.FAST),
        },
    )


async def test_hytec_scaler_does_not_change_mode_on_stage_by_default(
    hytec_scaler: Hytec8512Scaler,
):
    await hytec_scaler.stage()
    await hytec_scaler.unstage()
    get_mock_put(hytec_scaler.count_mode).assert_not_called()


async def test_hytec_scaler_sets_configured_stage_modes():
    async with init_devices(mock=True):
        hytec_scaler = Hytec8512Scaler(
            "TEST:", stage_mode=ScanMode.NORMAL, unstage_mode=ScanMode.FAST
        )
    await hytec_scaler.stage()
    assert await hytec_scaler.count_mode.get_value() == ScanMode.NORMAL
    await hytec_scaler.unstage()
    assert await hytec_scaler.count_mode.get_value() == ScanMode.FAST
