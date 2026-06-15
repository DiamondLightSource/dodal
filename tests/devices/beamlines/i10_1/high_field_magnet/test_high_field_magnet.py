import asyncio
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading

from dodal.devices.beamlines.i10_1.high_field_magnet.high_field_magnet import (
    FlyMagInfo,
    HighFieldMagnet,
)


@pytest.fixture
async def high_field_magnet() -> HighFieldMagnet:
    async with init_devices(mock=True):
        magnet = HighFieldMagnet(prefix="TEST:")
    return magnet


async def test_locate(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_setpoint, 5.0)
    set_mock_value(high_field_magnet.user_readback, 5.0)

    location = await high_field_magnet.locate()
    assert location["setpoint"] == 5.0
    assert location["readback"] == 5.0


async def test_stop_success(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 7.5)
    set_mock_value(high_field_magnet.user_readback, 1.5)
    await high_field_magnet.stop()
    assert high_field_magnet._set_success is False
    assert await high_field_magnet.user_setpoint.get_value() == 1.5


async def test_set_raises_runtime_error_when_stopped(
    high_field_magnet: HighFieldMagnet,
):
    set_mock_value(high_field_magnet.user_readback, -5.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)
    set_mock_value(high_field_magnet.ramp_up_time, 1.0)
    status = high_field_magnet.set(5.0)

    assert status is not None
    await asyncio.sleep(0)
    with pytest.raises(
        RuntimeError, match=f"Device {high_field_magnet.name} was stopped."
    ):
        await high_field_magnet.stop(success=False)
        await status


async def test_set_raises_on_zero_sweep_rate(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 0.0)

    with pytest.raises(ValueError, match="zero speed."):
        status = high_field_magnet.set(10.0)
        await status


@pytest.mark.parametrize(
    "new_position,sweep_rate,ramp_up_time",
    [
        (10.0, 1.0, 1.0),
        (5.0, 0.5, 0.2),
        (20.0, 2.0, 0.5),
    ],
)
async def test_set_calculates_correct_timeout(
    high_field_magnet: HighFieldMagnet, new_position, sweep_rate, ramp_up_time
):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, sweep_rate)
    set_mock_value(high_field_magnet.ramp_up_time, ramp_up_time)
    set_mock_value(high_field_magnet.user_setpoint, 0.0)

    high_field_magnet.movable_logic.move = AsyncMock()
    await high_field_magnet.set(new_position)
    expected_timeout = new_position / sweep_rate + 2 * ramp_up_time + DEFAULT_TIMEOUT
    high_field_magnet.movable_logic.move.assert_called_with(
        new_position=new_position, timeout=expected_timeout
    )


async def test_prepare(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    fly_info = FlyMagInfo(start_position=1.0, end_position=10.0, sweep_rate=2.0)
    await high_field_magnet.prepare(fly_info)
    assert high_field_magnet._fly_info == fly_info
    assert await high_field_magnet.user_setpoint.get_value() == 1.0
    assert await high_field_magnet.sweep_rate.get_value() == 2.0


async def test_kickoff_without_prepare_raises(high_field_magnet: HighFieldMagnet):
    with pytest.raises(RuntimeError, match="Magnet must be prepared"):
        await high_field_magnet.kickoff()


async def test_kickoff_after_prepare(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    fly_info = FlyMagInfo(start_position=1.0, end_position=10.0, sweep_rate=2.0)

    await high_field_magnet.prepare(fly_info)

    kickoff_status = high_field_magnet.kickoff()
    assert isinstance(kickoff_status, AsyncStatus)


async def test_complete_without_kickoff_raises(high_field_magnet: HighFieldMagnet):
    with pytest.raises(RuntimeError, match="kickoff not called"):
        high_field_magnet.complete()


async def test_complete_after_kickoff(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    fly_info = FlyMagInfo(start_position=1.0, end_position=10.0, sweep_rate=2.0)

    await high_field_magnet.prepare(fly_info)

    await high_field_magnet.kickoff()

    complete_status = high_field_magnet.complete()
    assert complete_status is high_field_magnet._fly_status


async def test_read(high_field_magnet: HighFieldMagnet):
    await high_field_magnet.user_setpoint.set(5.0)
    await assert_reading(
        high_field_magnet,
        expected_reading={"magnet": {"value": 5.0}},
    )


@pytest.mark.parametrize(
    "setpoint,readback,tolerance,expected",
    [
        (10.0, 10.005, 0.01, True),  # test positive tolerance
        (10.0, 9.995, 0.01, True),
        (10.0, 10.02, 0.01, False),
        (10.0, 0.9, 0.01, False),
        (10.0, 9.995, -0.01, True),  # test negative tolerance
        (10.0, 10.0005, -0.01, True),
        (10.0, 9.98, -0.01, False),
        (10.0, 10.1, -0.01, False),
    ],
)
async def test_tolerance_logic_within_tolerance(
    high_field_magnet: HighFieldMagnet, setpoint, readback, tolerance, expected
):
    result = high_field_magnet._within_tolerance(
        setpoint=setpoint, readback=readback, tolerance=tolerance
    )
    assert result is expected


async def test_tolerance_logic_stop_clears_set_success_and_restores_setpoint(
    high_field_magnet: HighFieldMagnet,
):
    set_mock_value(high_field_magnet.movable_logic.readback, 7.5)
    set_mock_value(high_field_magnet.movable_logic.readback, 1.5)
    await high_field_magnet.stop()
    assert high_field_magnet._set_success is False
    assert await high_field_magnet.movable_logic.setpoint.get_value() == 1.5


async def test_tolerance_logic_calculate_timeout(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.sweep_rate, 0.1)
    set_mock_value(high_field_magnet.ramp_up_time, 0.1)
    timeout = await high_field_magnet.movable_logic.calculate_timeout(
        old_position=0.0, new_position=10.0
    )
    expected_timeout = 10.0 / 0.1 + 2 * 0.1 + DEFAULT_TIMEOUT
    assert timeout == expected_timeout


async def test_tolerance_logic_calculate_timeout_with_zero_speed(
    high_field_magnet: HighFieldMagnet,
):
    set_mock_value(high_field_magnet.sweep_rate, 0.0)
    with pytest.raises(ValueError, match="zero speed."):
        await high_field_magnet.movable_logic.calculate_timeout(
            old_position=0.0, new_position=10.0
        )


async def test_tolerance_logic_move(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.movable_logic.readback, 0.0)
    move_task = high_field_magnet.movable_logic.move(new_position=10.0, timeout=5.0)
    for value in [2.0, 5.0, 8.0, 9.5, 13.0]:
        set_mock_value(high_field_magnet.movable_logic.readback, value)
        await asyncio.sleep(0.0)
        assert await high_field_magnet.within_tolerance.get_value() is False
    set_mock_value(high_field_magnet.movable_logic.readback, 9.91)
    await move_task
    assert await high_field_magnet.within_tolerance.get_value() is True
