import asyncio

import ophyd_async.core
import pytest
from propcache import cached_property

from dodal.devices.moveable_logics import ToleranceMovableLogic

DummyMovableLogic = ophyd_async.core.MovableLogic(
    setpoint=ophyd_async.core.soft_signal_rw(float, initial_value=0.0),
    readback=ophyd_async.core.soft_signal_rw(float, initial_value=0.0),
)


class DummyToleranceMovable(ophyd_async.core.StandardMovable):
    def __init__(self, name: str = "") -> None:
        self.setpoint = ophyd_async.core.soft_signal_rw(float, initial_value=0.0)
        self.readback = ophyd_async.core.soft_signal_rw(float, initial_value=0.0)
        self.tolerance = ophyd_async.core.soft_signal_rw(float, initial_value=0.01)
        self.speed = ophyd_async.core.soft_signal_rw(float, initial_value=1.0)
        self.acc_time = ophyd_async.core.soft_signal_rw(float, initial_value=0.1)
        super().__init__(name=name)

    @cached_property
    def movable_logic(self):
        return ToleranceMovableLogic(
            setpoint=self.setpoint,
            readback=self.readback,
            tolerance=self.tolerance,
            speed=self.speed,
            acc_time=self.acc_time,
        )


@pytest.fixture
async def test_movable() -> ophyd_async.core.StandardMovable:
    async with ophyd_async.core.init_devices(mock=True):
        device = DummyToleranceMovable(name="test_movable")
    return device


async def test_tolerance_logic_within_tolerance_when_in_range(
    test_movable: DummyToleranceMovable,
):
    result = test_movable.movable_logic._within_tolerance(
        setpoint=10.0, readback=10.005, tolerance=0.01
    )
    assert result is True


async def test_tolerance_logic_within_tolerance_when_outside_range(
    test_movable: DummyToleranceMovable,
):
    result = test_movable.movable_logic._within_tolerance(
        setpoint=10.0, readback=10.02, tolerance=0.01
    )
    assert result is False


async def test_tolerance_logic_within_tolerance_with_negative_tolerance(
    test_movable: DummyToleranceMovable,
):
    result = test_movable.movable_logic._within_tolerance(
        setpoint=10.0, readback=9.995, tolerance=-0.01
    )
    assert result is True


async def test_tolerance_logic_stop_clears_set_success_and_restores_setpoint(
    test_movable: DummyToleranceMovable,
):
    ophyd_async.core.set_mock_value(test_movable.movable_logic.readback, 7.5)
    ophyd_async.core.set_mock_value(test_movable.movable_logic.readback, 1.5)
    await test_movable.stop()
    assert test_movable._set_success is False
    assert await test_movable.movable_logic.setpoint.get_value() == 1.5


async def test_tolerance_logic_calculate_timeout(test_movable: DummyToleranceMovable):
    timeout = await test_movable.movable_logic.calculate_timeout(
        old_position=0.0, new_position=10.0
    )
    expected_timeout = 10.0 / 1.0 + 2 * 0.1 + ophyd_async.core.DEFAULT_TIMEOUT
    assert timeout == expected_timeout


async def test_tolerance_logic_calculate_timeout_with_zero_speed(
    test_movable: DummyToleranceMovable,
):
    ophyd_async.core.set_mock_value(test_movable.movable_logic.speed, 0.0)
    with pytest.raises(ValueError, match="zero speed."):
        await test_movable.movable_logic.calculate_timeout(
            old_position=0.0, new_position=10.0
        )


async def test_tolerance_logic_move(test_movable: DummyToleranceMovable):
    ophyd_async.core.set_mock_value(test_movable.movable_logic.readback, 0.0)
    move_task = test_movable.movable_logic.move(new_position=10.0, timeout=5.0)
    for value in [2.0, 5.0, 8.0, 9.5, 13.0]:
        ophyd_async.core.set_mock_value(test_movable.movable_logic.readback, value)
        await asyncio.sleep(0.0)
        assert await test_movable.movable_logic.within_tolerance.get_value() is False
    ophyd_async.core.set_mock_value(test_movable.movable_logic.readback, 9.91)
    await move_task
    assert await test_movable.movable_logic.within_tolerance.get_value() is True
