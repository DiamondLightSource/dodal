from functools import cached_property

import pytest
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    StandardMovable,
    set_mock_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.core._movable import MoveTimeout

from dodal.devices.movable import MovableWithToleranceLogic, is_within_tolerance


class MovableWithToleranceImpl(StandardMovable[float]):
    def __init__(self, name: str = ""):
        self.tolerance = soft_signal_rw(float)
        self.user_setpoint = soft_signal_rw(float)
        self.user_readback, _ = soft_signal_r_and_setter(float)
        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> MovableWithToleranceLogic:
        return MovableWithToleranceLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            tolerance=self.tolerance,
        )


@pytest.fixture
async def movable_with_tolerance() -> MovableWithToleranceImpl:
    movable_with_tolerance = MovableWithToleranceImpl("movable_with_tolerance")
    # Setup mock to not use default as do not want the setpoint and readback to be in
    # sync for tests so we can correctly test threshold signal.
    await movable_with_tolerance.connect(mock=DeviceMock())
    return movable_with_tolerance


@pytest.mark.parametrize(
    "setpoint, readback, tolerance, expected_within_threshold",
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
async def test_is_within_tolerance(
    tolerance: float,
    setpoint: float,
    readback: float,
    expected_within_threshold: bool,
) -> None:
    assert (
        is_within_tolerance(setpoint=setpoint, readback=readback, tolerance=tolerance)
        == expected_within_threshold
    )


@pytest.mark.parametrize(
    "initial_readback, initial_setpoint, initial_within_tolerance",
    ((0, 0, True), (0, -10, False)),
    ids=("initial_within_tolerance[True]", "initial_within_tolerance[False]"),
)
async def test_movable_with_tolerance_logic_moves_to_setpoint_and_is_done_when_within_tolerance(
    initial_readback: float,
    initial_setpoint: float,
    initial_within_tolerance: bool,
    movable_with_tolerance: MovableWithToleranceImpl,
) -> None:
    tolerance = 0.1
    set_mock_value(movable_with_tolerance.tolerance, tolerance)

    set_mock_value(movable_with_tolerance.movable_logic.setpoint, initial_setpoint)
    set_mock_value(movable_with_tolerance.movable_logic.readback, initial_readback)
    assert (
        is_within_tolerance(initial_setpoint, initial_readback, tolerance)
        == initial_within_tolerance
    )
    setpoint = 10

    async with AsyncStatus(
        movable_with_tolerance.movable_logic.move(
            new_position=setpoint, timeout=MoveTimeout(1)
        )
    ) as move_status:
        # This prevents a race where the test proceeds before the move coroutine has
        # had a chance to execute its first steps.
        await wait_for_value(
            movable_with_tolerance.movable_logic.setpoint, setpoint, timeout=1
        )
        # Set some values between initial readback and final setpoint that are outside
        # the threshold to test signal is correct and status hasn't completed.
        for value in [2.0, 5.0, 9.5, 13.0, setpoint - tolerance * 1.01]:
            set_mock_value(movable_with_tolerance.movable_logic.readback, value)
            current_readback = await movable_with_tolerance.user_readback.get_value()
            assert (
                is_within_tolerance(
                    setpoint=setpoint, readback=current_readback, tolerance=tolerance
                )
                is False
            )
            assert move_status.done is False

        # Now move to a value within threshold.
        set_mock_value(
            movable_with_tolerance.movable_logic.readback, setpoint - tolerance
        )
        current_readback = await movable_with_tolerance.user_readback.get_value()
        assert is_within_tolerance(
            setpoint=setpoint, readback=current_readback, tolerance=tolerance
        )

        # Wait for the underlying move task to complete so no race condition.
        # This ensures the status has fully processed the tolerance condition
        # and transitioned to a finished state before asserting `done`.
        await move_status
        assert move_status.done is True
