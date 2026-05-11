from unittest.mock import AsyncMock

import pytest
from bluesky.protocols import Location
from ophyd_async.core import init_devices

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    InsertionDevicePolarisation,
    Pol,
)
from tests.devices.insertion_device.conftest import DummyApple2Controller

pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def mock_id_polarisation(
    mock_id_controller: DummyApple2Controller,
) -> InsertionDevicePolarisation:
    async with init_devices(mock=True):
        mock_id_polarisation = InsertionDevicePolarisation(
            id_controller=mock_id_controller,
        )
    return mock_id_polarisation


async def test_polarisation_set_calls_controller_methods(
    mock_id_controller: DummyApple2Controller,
    mock_id_polarisation: InsertionDevicePolarisation,
):
    mock_id_controller.polarisation.set = AsyncMock()
    pol = Pol.PC
    await mock_id_polarisation.set(pol=pol)
    mock_id_controller.polarisation.set.assert_called_once_with(
        pol, timeout=MAXIMUM_MOVE_TIME
    )


async def test_insertion_device_polarisation_locate(
    mock_id_controller: DummyApple2Controller,
    mock_id_polarisation: InsertionDevicePolarisation,
):
    pol = Pol.LH
    mock_id_controller.polarisation_setpoint.get_value = AsyncMock(return_value=pol)
    mock_id_controller.polarisation.get_value = AsyncMock(return_value=pol)
    location = await mock_id_polarisation.locate()
    assert location == Location(setpoint=pol, readback=pol)
