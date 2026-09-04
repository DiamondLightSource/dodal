from collections.abc import Iterable, Sequence
from decimal import Decimal

import numpy as np

from dodal.plans.scans.annotations import (
    MovableListOfPoints,
    MovableStartStep,
    MovableStartStopStep,
    Number,
    T,
)


def flatten(items: Iterable[Iterable[T]]) -> tuple[T, ...]:
    """Flatten one level of nested iterables."""
    return tuple(item for group in items for item in group)


def _round_list_elements(
    stepped_list: list[Number], params: list[Number]
) -> list[Number]:
    decimals = [Decimal(str(param)) for param in params]
    exponents = [d.as_tuple().exponent for d in decimals]
    decimal_places = [-exponent for exponent in exponents]  # type: ignore
    max_decimal_places = max(decimal_places)
    return np.round(stepped_list, decimals=max_decimal_places).tolist()


def _make_stepped_list_step(start: float, stop: float, step: float) -> list[Number]:
    if abs(step) > abs(stop - start):
        step = stop - start
    step = abs(step) * np.sign(stop - start)
    stepped_list = np.arange(start, stop, step).tolist()
    if abs((stepped_list[-1] + step) - stop) <= abs(step * 0.05):
        stepped_list.append(stepped_list[-1] + step)
    rounded_stepped_list = _round_list_elements(
        stepped_list=stepped_list, params=[start, stop, step]
    )
    return rounded_stepped_list


def _make_stepped_list_num(start: float, step: float, num: int) -> list[Number]:
    if num == 0 or step == 0:
        raise ValueError(
            f"Number of points ({num}) and number of steps ({step}) cannot be zero."
        )
    stepped_list = [start + (n * step) for n in range(num)]
    rounded_stepped_list = _round_list_elements(
        stepped_list=stepped_list, params=[start, step]
    )
    return rounded_stepped_list


def make_step_scan_args_and_shape(
    trajectory: MovableStartStopStep, extra_trajectories: Sequence[MovableStartStep]
) -> tuple[list[MovableListOfPoints], tuple[int, ...]]:
    """Convert [x, (1, 5, 1), ...] to [x, [1, 2, 3, 4, 5], ...]."""
    movable, start, stop, step = trajectory

    movable_values = _make_stepped_list_step(start, stop, step)
    shape = [len(movable_values)]
    step_scan_args: list[MovableListOfPoints] = [(movable, movable_values)]

    for et in extra_trajectories:
        movable, start, step = et
        # For a non-grid scan, subsequent axes have the same number
        # of points as the first axis.
        movable_values = _make_stepped_list_num(start, step, shape[0])
        step_scan_args.append((movable, movable_values))

    return step_scan_args, tuple(shape)


def make_step_grid_scan_args_and_shape(
    params: Sequence[MovableStartStopStep],
) -> tuple[list[MovableListOfPoints], tuple[int, ...]]:
    """Convert [x, (1, 5, 1), ...] to [x, [1, 2, 3, 4, 5], ...]."""
    step_scan_args: list[MovableListOfPoints] = []
    shape: list[int] = []

    for trajectory in params:
        movable, start, stop, step = trajectory
        movable_values = _make_stepped_list_step(start, stop, step)
        shape.append(len(movable_values))
        step_scan_args.append((movable, movable_values))

    return step_scan_args, tuple(shape)
