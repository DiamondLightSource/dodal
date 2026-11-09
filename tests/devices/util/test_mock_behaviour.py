import asyncio

import pytest
from ophyd_async.core import (
    Device,
    StrictEnum,
    default_mock_class,
    init_devices,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.util.mock_behaviour import reset_signal_on_update_mock_factory


class MockState(StrictEnum):
    OTHER = "Other"
    ACTIVE = "Active"
    IDLE = "Idle"


@default_mock_class(
    reset_signal_on_update_mock_factory("state", MockState.ACTIVE, MockState.IDLE)
)
class MockDevice(Device):
    def __init__(self, name: str = ""):
        self.state = epics_signal_r(MockState, "MOCK:STATE")
        super().__init__(name)


@pytest.fixture
async def mock_device():
    with init_devices(mock=True):
        mock_device = MockDevice()
    return mock_device


async def test_reset_signal_on_update_mock_factory_sets_initial_signal(
    mock_device: MockDevice,
):
    # Default would use OTHER in this case because it is first in the enum. Check once
    # connected it got set to IDLE.
    assert await mock_device.state.get_value() == MockState.IDLE


async def test_reset_signal_on_update_mock_factory_resets_signal(
    mock_device: MockDevice,
):
    set_mock_value(mock_device.state, MockState.ACTIVE)
    assert await mock_device.state.get_value() == MockState.ACTIVE
    await asyncio.sleep(0.02)
    assert await mock_device.state.get_value() == MockState.IDLE


@pytest.mark.asyncio
async def test_reset_signal_on_update_mock_factory_ignores_non_matching_reading(
    mock_device: MockDevice,
):
    set_mock_value(mock_device.state, MockState.OTHER)
    await asyncio.sleep(0.02)
    assert await mock_device.state.get_value() == MockState.OTHER


async def test_scaler_controller_multiple_connects_has_one_subscribe(
    mock_device: MockDevice,
) -> None:
    expected_subscribers = 1
    number_of_subscribers = len(mock_device.state._get_cache()._listeners)
    assert number_of_subscribers == expected_subscribers
    # Test if we connect again if another subscriber is added, checking for memory leaks.
    for _ in range(3):
        await mock_device.connect(mock=True)
        assert len(mock_device.state._get_cache()._listeners) == expected_subscribers

    def dummy_sub(value):
        pass

    # Now add new subscribe callback to make sure it does go up and not checking the
    # wrong thing.
    mock_device.state.subscribe(dummy_sub)
    assert len(mock_device.state._get_cache()._listeners) == 2
