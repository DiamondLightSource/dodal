import pytest
from ophyd_async.core import (
    DeviceMock,
    init_devices,
    set_mock_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.movable import MovableWithTolerance


class MovableWithToleranceImpl(MovableWithTolerance):
    def __init__(self, name: str = ""):
        self.custom_tolerance = soft_signal_rw(float)
        self.custom_setpoint = soft_signal_rw(float)
        self.custom_readback, _ = soft_signal_r_and_setter(float)
        super().__init__(
            tolerance=self.custom_tolerance,
            setpoint=self.custom_setpoint,
            readback=self.custom_readback,
            name=name,
        )


@pytest.fixture
async def movable_with_tolerance() -> MovableWithToleranceImpl:
    with init_devices(mock=True):
        movable_with_tolerance = MovableWithToleranceImpl()
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
async def test_movable_with_tolerance_within_threshold(
    movable_with_tolerance: MovableWithToleranceImpl,
    tolerance: float,
    setpoint: float,
    readback: float,
    expected_within_threshold: bool,
) -> None:
    # Setup mock to not use default as do not want the setpoint and readback to be the
    # same for tests so we can correctly test threshold signal.
    await movable_with_tolerance.connect(mock=DeviceMock())
    set_mock_value(movable_with_tolerance.custom_tolerance, tolerance)
    set_mock_value(movable_with_tolerance.custom_setpoint, setpoint)
    set_mock_value(movable_with_tolerance.custom_readback, readback)
    assert (
        await movable_with_tolerance.within_tolerance.get_value()
        == expected_within_threshold
    )


async def test_movable_with_tolerance_logic_move(
    movable_with_tolerance: MovableWithToleranceImpl,
) -> None:
    set_mock_value(movable_with_tolerance.movable_logic.readback, 0.0)
    move_task = movable_with_tolerance.movable_logic.move(
        new_position=10.0, timeout=5.0
    )
    for value in [2.0, 5.0, 8.0, 9.5, 13.0]:
        set_mock_value(movable_with_tolerance.movable_logic.readback, value)
        assert await movable_with_tolerance.within_tolerance.get_value() is False
    set_mock_value(movable_with_tolerance.movable_logic.readback, 9.91)
    await move_task
    assert await movable_with_tolerance.within_tolerance.get_value() is True


async def test_movable_with_tolerance_sub_class_signal_names_are_not_renamed(
    movable_with_tolerance: MovableWithToleranceImpl,
) -> None:
    assert (
        movable_with_tolerance.custom_setpoint.name
        == "movable_with_tolerance-custom_setpoint"
    )
    assert (
        movable_with_tolerance.custom_tolerance.name
        == "movable_with_tolerance-custom_tolerance"
    )
    # Readback is the exception as renamed by StandardMovable to be device name
    assert movable_with_tolerance.custom_readback.name == "movable_with_tolerance"
