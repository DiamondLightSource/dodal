import re

import pytest
from ophyd_async.sim import SimMotor

from dodal.plans.scans.types import MovableStartStep, MovableStartStopStep
from dodal.plans.scans.utils import (
    _make_stepped_list_num,
    _make_stepped_list_step,
    _round_list_elements,
    make_step_grid_scan_args_and_shape,
    make_step_scan_args_and_shape,
)


@pytest.mark.parametrize(
    "trajectories_start_stop_step, trajectories_start_stop, expected_shape, expected_length",
    [
        ([("x_axis", 0, 10, 1)], [("y_axis", 0, 5)], (11,), 2),
        ([("x_axis", 0, 10, 1)], [("y_axis", 0, 1)], (11,), 2),
    ],
    indirect=["trajectories_start_stop_step", "trajectories_start_stop"],
)
def test_make_step_scan_args_and_shape(
    trajectories_start_stop_step: list[MovableStartStopStep],
    trajectories_start_stop: list[MovableStartStep],
    expected_shape: tuple[int, ...],
    expected_length: int,
):
    args, shape = make_step_scan_args_and_shape(
        trajectory=trajectories_start_stop_step[0],
        extra_trajectories=trajectories_start_stop,
    )
    assert len(args) == expected_length
    assert shape == expected_shape


@pytest.mark.parametrize(
    "trajectories_start_stop_step, expected_shape, expected_length",
    [
        ([("x_axis", 0, 10, 1), ("y_axis", 0, 5, 1)], (11, 6), 2),
    ],
    indirect=["trajectories_start_stop_step"],
)
def test_make_step_grid_scan_args_and_shape(
    trajectories_start_stop_step: list[MovableStartStopStep],
    expected_shape: tuple[int, ...],
    expected_length: int,
):
    args, shape = make_step_grid_scan_args_and_shape(
        params=trajectories_start_stop_step
    )
    assert len(args) == expected_length
    assert shape == expected_shape


@pytest.mark.parametrize(
    "stepped_list, params, expected_rounded_element",
    (
        [[0.1234, 1.1234, 2.1234], [0.123, 2.123, 1], 0.123],
        [[0.1234, 1.1234, 2.1234], [0.12, 2.12, 1], 0.12],
        [[0.1234, 1.1234, 2.1234], [0.1, 2.1, 1], 0.1],
        [[0.1234, 1.1234, 2.1234], [0, 2, 1], 0],
    ),
)
def test_round_list_elements(
    stepped_list: list[float], params: list[float], expected_rounded_element: float
):
    rounded_list = _round_list_elements(stepped_list, params)
    assert rounded_list[0] == expected_rounded_element


@pytest.mark.parametrize(
    "start, stop, step",
    (
        [-1, 1, 0.1],
        [-2, 2, 0.2],
        [1, -1, -0.1],
        [2, -2, -0.2],
        [1, -1, 0.1],
        [2, -2, 0.2],
    ),
)
def test_make_stepped_list_step(
    x_axis: SimMotor, start: float, stop: float, step: float
):
    stepped_list = _make_stepped_list_step((x_axis, start, stop, step))
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_step_with_large_step(x_axis: SimMotor):
    stepped_list = _make_stepped_list_step((x_axis, 0, 1, 5))
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 2
    assert stepped_list[0] == 0
    assert stepped_list[-1] == 1


@pytest.mark.parametrize("start, step", ([-1, 0.1], [-2, 0.2], [1, -0.1], [2, -0.2]))
def test_make_stepped_list_num(x_axis: SimMotor, start: float, step: float):
    num = 21
    stepped_list = _make_stepped_list_num((x_axis, start, step, num))
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == num
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_num_fails_when_num_is_zero(x_axis: SimMotor):
    start = stop = 1.1
    step = 0.25
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Start and stop values cannot be the same. "
            "Expected (movable, start, stop, step). "
            f"Received (x_axis, {start}, {stop}, {step})."
        ),
    ):
        _make_stepped_list_step((x_axis, start, stop, step))


def test_make_stepped_list_num_fails_when_given_equal_start_and_stop_values(
    x_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Number of steps and number of points cannot be zero. "
            "Expected (movable, start, step, num). "
            "Received (x_axis, 1, 0, 0)."
        ),
    ):
        _make_stepped_list_num((x_axis, 1, 0, 0))
