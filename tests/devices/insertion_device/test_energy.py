from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from ophyd_async.core import FlyMotorInfo, get_mock_put, init_devices, set_mock_value

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    BeamEnergy,
    InsertionDeviceEnergy,
    Pol,
    UndulatorGap,
    UndulatorGateStatus,
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


@pytest.mark.parametrize(
    "start_gap, end_gap,acceleration_time,time_for_move",
    [
        (21.0, 25.0, 0.5, 1.0),
        (35.0, 15.0, 1.5, 9.0),
    ],
)
async def test_insertion_device_energy_prepare_success(
    mock_id_controller: DummyApple2Controller,
    mock_id_energy: InsertionDeviceEnergy,
    start_gap,
    end_gap,
    acceleration_time,
    time_for_move,
):
    set_mock_value(mock_id_controller.apple2().gap().max_velocity, 30)
    set_mock_value(mock_id_controller.apple2().gap().min_velocity, 1)
    set_mock_value(mock_id_controller.apple2().gap().low_limit_travel, 0)
    set_mock_value(mock_id_controller.apple2().gap().high_limit_travel, 200)
    set_mock_value(mock_id_controller.apple2().gap().gate, UndulatorGateStatus.CLOSE)
    set_mock_value(
        mock_id_controller.apple2().gap().acceleration_time, acceleration_time
    )
    mock_id_controller._polarisation_setpoint_set(Pol.LH)
    mock_id_energy.set = AsyncMock()
    mid_gap_position = end_gap + start_gap / 2.0
    mock_id_controller.gap_energy_motor_converter = Mock(
        side_effect=[start_gap, end_gap, mid_gap_position]
    )
    fly_info = FlyMotorInfo(
        start_position=700, end_position=800, time_for_move=time_for_move
    )
    await mock_id_energy.prepare(fly_info)
    velocity = (end_gap - start_gap) / time_for_move
    ramp_up_start = start_gap - acceleration_time * velocity / 2.0
    mock_id_energy.set.assert_awaited_once_with(energy=750)
    get_mock_put(
        mock_id_controller.apple2().gap().user_setpoint
    ).assert_awaited_once_with(str(ramp_up_start), wait=True)

    assert await mock_id_controller.apple2().gap().velocity.get_value() == abs(velocity)


async def test_insertion_deviceenergy_kickoff_call_gap_kickoff(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_gap: UndulatorGap,
):
    mock_id_gap.kickoff = AsyncMock()
    await mock_id_energy.kickoff()
    mock_id_gap.kickoff.assert_awaited_once()


def test_insertion_device_energy_complete_call_gap_complete(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_gap: UndulatorGap,
):
    mock_id_gap.complete = MagicMock()
    mock_id_energy.complete()
    mock_id_gap.complete.assert_called_once()
