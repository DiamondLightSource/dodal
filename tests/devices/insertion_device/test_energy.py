import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import prepare
from ophyd_async.core import (
    AsyncStatus,
    FlyMotorInfo,
    WatchableAsyncStatus,
    get_mock_put,
    init_devices,
    set_mock_attr,
    set_mock_value,
)

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
async def mock_beam_energy(
    mock_id_energy: InsertionDeviceEnergy, mock_pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    async with init_devices(mock=True):
        mock_beam_energy = BeamEnergy(id_energy=mock_id_energy, mono=mock_pgm.energy)
    return mock_beam_energy


async def test_mock_beam_controller_set_moves_both_devices(
    mock_beam_energy: BeamEnergy,
    mock_id_energy: InsertionDeviceEnergy,
    mock_pgm: PlaneGratingMonochromator,
):
    mock_id_energy_set = set_mock_attr(mock_id_energy, "set", AsyncMock())
    mock_pgm_energy_set = set_mock_attr(mock_pgm.energy, "set", AsyncMock())

    await mock_beam_energy.set(100.0)

    mock_id_energy_set.assert_called_once_with(energy=100.0)
    mock_pgm_energy_set.assert_called_once_with(100.0)


async def test_insertion_device_energy_set(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_controller: DummyApple2Controller,
):
    mock_set = set_mock_attr(mock_id_controller.energy, "set", AsyncMock())

    await mock_id_energy.set(1500.0)

    mock_set.assert_awaited_once_with(1500.0, timeout=MAXIMUM_MOVE_TIME)


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
    gap = mock_id_controller.apple2_ref().gap_ref()
    set_mock_value(gap.motor.max_velocity, 30)
    set_mock_value(gap.motor.min_velocity, 1)
    set_mock_value(gap.motor.low_limit_travel, 0)
    set_mock_value(gap.motor.high_limit_travel, 200)
    set_mock_value(gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(gap.motor.acceleration_time, acceleration_time)
    mock_id_controller._polarisation_setpoint_set(Pol.LH)
    mock_set = set_mock_attr(mock_id_energy, "set", AsyncMock())
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
    mock_set.assert_awaited_once_with(energy=750)
    get_mock_put(gap.motor.user_setpoint).assert_awaited_once_with(ramp_up_start)

    assert await gap.motor.velocity.get_value() == abs(velocity)


async def test_insertion_deviceenergy_kickoff_call_gap_kickoff(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_gap: UndulatorGap,
):
    mock_kickoff = set_mock_attr(mock_id_gap, "kickoff", AsyncMock())
    await mock_id_energy.kickoff()
    mock_kickoff.assert_awaited_once()


async def test_insertion_device_energy_complete_calls_gap_complete(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_gap: UndulatorGap,
):
    expected_status = MagicMock(spec=WatchableAsyncStatus)
    mock_complete = set_mock_attr(
        mock_id_gap, "complete", MagicMock(return_value=expected_status)
    )
    status = mock_id_energy.complete()

    assert status is expected_status
    mock_complete.assert_called_once_with()


async def test_insertion_device_energy_prepare_success_in_run_engine(
    run_engine: RunEngine, mock_id_energy: InsertionDeviceEnergy
):
    fly_motor_info = FlyMotorInfo(
        start_position=600,
        end_position=700,
        time_for_move=60,
    )
    run_engine(prepare(mock_id_energy, fly_motor_info, wait=True))


async def test_beam_energy_prepare_success(
    run_engine: RunEngine,
    mock_beam_energy: BeamEnergy,
    mock_pgm: PlaneGratingMonochromator,
    mock_id_energy: InsertionDeviceEnergy,
):
    fly_info = FlyMotorInfo(start_position=700, end_position=800, time_for_move=10)
    mock_id_energy_prepare = set_mock_attr(mock_id_energy, "prepare", AsyncMock())
    mock_pgm_energy_prepare = set_mock_attr(mock_pgm.energy, "prepare", AsyncMock())
    run_engine(prepare(mock_beam_energy, fly_info))
    mock_id_energy_prepare.assert_awaited_once_with(fly_info)
    mock_pgm_energy_prepare.assert_awaited_once_with(fly_info)


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_beam_energy_kickoff_set_correct_delay(
    mock_sleep: AsyncMock,
    mock_beam_energy: BeamEnergy,
    mock_pgm: PlaneGratingMonochromator,
    mock_id_gap: UndulatorGap,
    mock_id_controller: DummyApple2Controller,
):
    mock_id_controller.gap_energy_motor_converter = Mock(side_effect=[21.0, 20, 22.0])
    mock_id_controller.phase_energy_motor_converter = Mock(side_effect=[22.0, 22, 22.0])
    fly_info = FlyMotorInfo(start_position=700, end_position=800, time_for_move=10)
    id_acc_time = 3
    pgm_acc_time = 1
    set_mock_value(mock_id_gap.motor.max_velocity, 30)
    set_mock_value(mock_id_gap.motor.min_velocity, 0.1)
    set_mock_value(mock_id_gap.motor.acceleration_time, id_acc_time)
    set_mock_value(mock_pgm.energy.max_velocity, 30)
    set_mock_value(mock_id_gap.motor.low_limit_travel, 0)
    set_mock_value(mock_id_gap.motor.high_limit_travel, 200)
    set_mock_value(mock_pgm.energy.low_limit_travel, 0)
    set_mock_value(mock_pgm.energy.high_limit_travel, 1000)
    set_mock_value(mock_pgm.energy.acceleration_time, pgm_acc_time)
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.CLOSE)
    mock_id_gap_kickoff = set_mock_attr(mock_id_gap, "kickoff", AsyncMock())
    mock_pgm_energy_kickoff = set_mock_attr(mock_pgm.energy, "kickoff", AsyncMock())
    await mock_beam_energy.prepare(fly_info)
    await mock_beam_energy.kickoff()
    mock_sleep.assert_called_with(pgm_acc_time - id_acc_time)
    mock_id_gap_kickoff.assert_awaited_once()
    mock_pgm_energy_kickoff.assert_awaited_once()


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_energysetter_complete(
    mock_sleep: AsyncMock,
    mock_beam_energy: BeamEnergy,
    mock_pgm: PlaneGratingMonochromator,
    mock_id_energy: InsertionDeviceEnergy,
) -> None:
    id_complete_event = asyncio.Event()
    pgm_complete_event = asyncio.Event()

    @AsyncStatus.wrap
    async def wait_for_id_complete() -> None:
        await id_complete_event.wait()

    @AsyncStatus.wrap
    async def wait_for_pgm_complete() -> None:
        await pgm_complete_event.wait()

    set_mock_attr(mock_id_energy, "kickoff", AsyncMock())
    set_mock_attr(
        mock_id_energy, "complete", MagicMock(return_value=wait_for_id_complete())
    )

    set_mock_attr(mock_pgm.energy, "kickoff", AsyncMock())
    set_mock_attr(
        mock_pgm.energy, "complete", MagicMock(return_value=wait_for_pgm_complete())
    )

    await mock_beam_energy.prepare(
        FlyMotorInfo(start_position=700, end_position=800, time_for_move=10)
    )
    await mock_beam_energy.kickoff()

    energy_setter_fly_status = mock_beam_energy.complete()

    assert not energy_setter_fly_status.done

    id_complete_event.set()
    await asyncio.sleep(0)
    assert not energy_setter_fly_status.done

    pgm_complete_event.set()
    await energy_setter_fly_status

    assert energy_setter_fly_status.done
