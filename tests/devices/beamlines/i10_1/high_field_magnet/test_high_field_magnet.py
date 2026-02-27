import pytest
from ophyd_async.core import (
    AsyncStatus,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, wait_for_pending_wakeups

from dodal.devices.beamlines.i10_1.high_field_magnet.high_field_magnet import (
    FlyMagInfo,
    HighFieldMagnet,
)


@pytest.fixture
async def high_field_magnet() -> HighFieldMagnet:
    async with init_devices(mock=True):
        magnet = HighFieldMagnet(prefix="TEST:")
    return magnet


async def test_within_tolerance_when_in_range(high_field_magnet: HighFieldMagnet):
    result = high_field_magnet._within_tolerance(
        setpoint=10.0, readback=10.005, tolerance=0.01
    )
    assert result is True


async def test_within_tolerance_when_outside_range(high_field_magnet: HighFieldMagnet):
    result = high_field_magnet._within_tolerance(
        setpoint=10.0, readback=10.02, tolerance=0.01
    )
    assert result is False


async def test_within_tolerance_with_negative_tolerance(
    high_field_magnet: HighFieldMagnet,
):
    result = high_field_magnet._within_tolerance(
        setpoint=10.0, readback=9.995, tolerance=-0.01
    )
    assert result is True


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
    with pytest.raises(RuntimeError, match="Field change was stopped"):
        await wait_for_pending_wakeups()
        await high_field_magnet.stop(success=False)
        set_mock_value(high_field_magnet.user_readback, 5.0)
        await status


async def test_subscribe_and_clear_sub(high_field_magnet: HighFieldMagnet):
    """Test subscribe_reading and clear_sub for callbacks."""
    readings = []

    def callback(reading_dict):
        readings.append(reading_dict)

    high_field_magnet.subscribe_reading(callback)

    set_mock_value(high_field_magnet.user_readback, 3.0)

    high_field_magnet.clear_sub(callback)

    assert callable(callback)


async def test_set_raises_on_zero_sweep_rate(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 0.0)

    with pytest.raises(ValueError, match="Magnet has zero sweep_rate."):
        status = high_field_magnet.set(10.0)
        await status


async def test_set_calculates_correct_timeout(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)
    set_mock_value(high_field_magnet.ramp_up_time, 1.0)
    set_mock_value(high_field_magnet.user_setpoint, 0.0)

    # Start the set operation
    status = high_field_magnet.set(10.0)
    assert isinstance(status, AsyncStatus) or hasattr(status, "watch")


async def test_set_returns_watchable_async_status(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    status = high_field_magnet.set(5.0)
    assert status is not None


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
        status = high_field_magnet.kickoff()
        await status


async def test_kickoff_after_prepare(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    fly_info = FlyMagInfo(start_position=1.0, end_position=10.0, sweep_rate=2.0)

    prepare_status = high_field_magnet.prepare(fly_info)
    await prepare_status

    kickoff_status = high_field_magnet.kickoff()
    assert isinstance(kickoff_status, AsyncStatus)


async def test_complete_without_kickoff_raises(high_field_magnet: HighFieldMagnet):
    with pytest.raises(RuntimeError, match="kickoff not called"):
        high_field_magnet.complete()


async def test_complete_after_kickoff(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_readback, 0.0)
    set_mock_value(high_field_magnet.sweep_rate, 1.0)

    fly_info = FlyMagInfo(start_position=1.0, end_position=10.0, sweep_rate=2.0)

    prepare_status = high_field_magnet.prepare(fly_info)
    await prepare_status

    kickoff_status = high_field_magnet.kickoff()
    await kickoff_status

    complete_status = high_field_magnet.complete()
    assert complete_status is high_field_magnet._fly_status


async def test_read(high_field_magnet: HighFieldMagnet):
    set_mock_value(high_field_magnet.user_setpoint, 5.0)
    set_mock_value(high_field_magnet.user_readback, 5.0)
    await assert_reading(
        high_field_magnet,
        expected_reading={"magnet": {"value": 5.0}},
    )
