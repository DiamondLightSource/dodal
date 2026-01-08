from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    BeamEnergy,
    InsertionDeviceEnergy,
)
from dodal.devices.pgm import PlaneGratingMonochromator

from .conftest import DummyApple2Controller

pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def beam_energy(
    mock_id_energy: InsertionDeviceEnergy, mock_pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    async with init_devices(mock=True):
        beam_energy = BeamEnergy(id_energy=mock_id_energy, mono=mock_pgm.energy)
    return beam_energy


async def test_beam_energy_set_moves_both_devices(
    beam_energy: BeamEnergy,
    mock_id_energy: InsertionDeviceEnergy,
    mock_pgm: PlaneGratingMonochromator,
):
    mock_id_energy.set = AsyncMock()
    mock_pgm.energy.set = AsyncMock()

    await beam_energy.set(100.0)

    mock_id_energy.set.assert_called_once_with(energy=100.0)
    mock_pgm.energy.set.assert_called_once_with(100.0)


async def test_insertion_device_energy_set(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_controller: DummyApple2Controller,
):
    mock_id_controller.energy.set = AsyncMock()

    await mock_id_energy.set(1500.0)

    mock_id_controller.energy.set.assert_awaited_once_with(
        1500.0, timeout=MAXIMUM_MOVE_TIME
    )
