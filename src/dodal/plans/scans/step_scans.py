import math
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import bluesky.plans as bp
import numpy as np
from bluesky.protocols import NamedMovable, Readable
from bluesky.utils import CustomPlanMetadata

from dodal.common import MsgGenerator

StepScanArg = NamedMovable | float | int

# Include a final point that overshoots stop by up to this fraction of a step.
_STOP_TOLERANCE = 0.05


def _decimal_places(*values: float) -> int:
    """Most decimal places of any of the values, e.g. (1, 0.5, 0.25) -> 2."""
    return max(0, *(-int(Decimal(str(v)).as_tuple().exponent) for v in values))


def _positions(start: float, step: float, num: int, decimal_places: int) -> list[float]:
    """`num` positions from `start` in increments of `step`, rounded to remove float
    error.
    """
    return np.round(start + step * np.arange(num), decimal_places).tolist()


def _make_stepped_list_step(start: float, stop: float, step: float) -> list[float]:
    """Positions from `start` towards `stop`, ignoring the sign of `step`. `stop` is
    included if reached to within 5% of a step.
    """
    if start == stop:
        raise ValueError(
            f"Start ({start}) and stop ({stop}) values cannot be the same."
        )
    if step == 0:
        raise ValueError("Step cannot be zero.")
    decimal_places = _decimal_places(start, stop, step)
    span = stop - start
    step = math.copysign(min(abs(step), abs(span)), span)
    # Round away floating point error so the tolerance boundary is deterministic.
    num = math.floor(round(span / step + _STOP_TOLERANCE, 9)) + 1
    return _positions(start, step, num, decimal_places)


def _make_stepped_list_num(start: float, step: float, num: int) -> list[float]:
    """`num` positions from `start` in increments of `step`."""
    return _positions(start, step, num, _decimal_places(start, step))


def _group_args_by_movable(
    args: Sequence[StepScanArg],
) -> list[tuple[NamedMovable, list[float | int]]]:
    """Split flat args into (movable, [numbers]) groups, e.g.
    `(x, 0, 10, 1, y, 5, 0.5)` -> `[(x, [0, 10, 1]), (y, [5, 0.5])]`.
    """
    if not args:
        raise ValueError("No movables provided, at least one axis must be scanned.")

    groups: list[tuple[NamedMovable, list[float | int]]] = []
    for arg in args:
        if isinstance(arg, NamedMovable):
            groups.append((arg, []))
        elif not groups:
            raise ValueError(
                f"Expected a movable as the first argument after detectors, got {arg!r}."
            )
        elif not isinstance(arg, int | float):
            raise TypeError(
                f"Expected a movable or a number, got {arg!r} of type "
                f"{type(arg).__name__}."
            )
        else:
            groups[-1][1].append(arg)
    return groups


def _make_step_scan_args(args: Sequence[StepScanArg], grid: bool) -> list[Any]:
    """Convert step scan args to list scan args, `[movable1, positions1, ...]`.

    Grid axes each take `start, stop, step`. Otherwise only the first axis does and
    the rest take `start, step`, with the same number of points as the first.
    """
    list_scan_args: list[Any] = []
    num_points = 0
    for i, (movable, params) in enumerate(_group_args_by_movable(args)):
        sets_num_points = grid or i == 0
        expected = ("start", "stop", "step") if sets_num_points else ("start", "step")
        if len(params) != len(expected):
            raise ValueError(
                f"You provided {len(params)} parameters for {movable.name}, rather "
                f"than {len(expected)} ({', '.join(expected)})."
            )
        if sets_num_points:
            positions = _make_stepped_list_step(*params)
            num_points = len(positions)
        else:
            positions = _make_stepped_list_num(*params, num=num_points)
        list_scan_args += [movable, positions]

    return list_scan_args


def _make_step_scan_md(
    plan_name: str,
    detectors: Sequence[Readable],
    args: Sequence[StepScanArg],
    md: CustomPlanMetadata | None,
    **plan_args: Any,
) -> CustomPlanMetadata:
    """Start document metadata recording the step scan as called, rather than the
    list scan it runs. User `metadata` takes priority.
    """
    return {
        "plan_name": plan_name,
        "plan_args": {
            "detectors": list(map(repr, detectors)),
            "args": [repr(a) if isinstance(a, NamedMovable) else a for a in args],
            **plan_args,
        },
        "detectors": [det.name for det in detectors],
        **(md or {}),
    }


def step_scan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    md: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan movables concurrently, using a step size rather than number of points.

    The first movable takes `start, stop, step`, which sets the number of points.
    Further movables take `start, step` and move with it.

    Args:
        detectors: Devices to read at every point.
        *args: `movable1, start1, stop1, step1, movable2, start2, step2, ...`
        md: Extra start document metadata, overriding the plan's own.

    Examples:
        11 points, `x` from 0 to 10 and `y` from 5 to 10::

            step_scan([det], x, 0, 10, 1, y, 5, 0.5)
    """
    list_scan_args = _make_step_scan_args(args, grid=False)
    md = _make_step_scan_md("step_scan", detectors, args, md)
    yield from bp.list_scan(detectors, *list_scan_args, md=md)


def step_rscan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    md: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """As `step_scan`, but relative to the current positions, returning to them at the
    end.

    Args:
        detectors: Devices to read at every point.
        *args: `movable1, start1, stop1, step1, movable2, start2, step2, ...`
        md: Extra start document metadata, overriding the plan's own.

    Examples:
        21 points, `x` from 1 below to 1 above its current position::

            step_rscan([det], x, -1, 1, 0.1)
    """
    list_scan_args = _make_step_scan_args(args, grid=False)
    md = _make_step_scan_md("step_rscan", detectors, args, md)
    yield from bp.rel_list_scan(detectors, *list_scan_args, md=md)


def step_grid_scan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    snake_axes: bool = True,
    md: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan a grid of movables, using a step size rather than number of points.

    Every movable takes `start, stop, step`. The first is the slowest axis.

    Args:
        detectors: Devices to read at every point.
        *args: `movable1, start1, stop1, step1, movable2, start2, stop2, step2, ...`
        snake_axes: Reverse every axis but the first on alternate passes.
        md: Extra start document metadata, overriding the plan's own.

    Examples:
        25 points, 5 rows of `y` from 0 to 2 by 5 columns of `x` from 0 to 1::

            step_grid_scan([det], y, 0, 2, 0.5, x, 0, 1, 0.25)
    """
    list_scan_args = _make_step_scan_args(args, grid=True)
    md = _make_step_scan_md(
        "step_grid_scan", detectors, args, md, snake_axes=snake_axes
    )
    yield from bp.list_grid_scan(
        detectors, *list_scan_args, snake_axes=snake_axes, md=md
    )


def step_grid_rscan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    snake_axes: bool = True,
    md: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """As `step_grid_scan`, but relative to the current positions, returning to them
    at the end.

    Args:
        detectors: Devices to read at every point.
        *args: `movable1, start1, stop1, step1, movable2, start2, stop2, step2, ...`
        snake_axes: Reverse every axis but the first on alternate passes.
        md: Extra start document metadata, overriding the plan's own.

    Examples:
        25 points, 1 either side of the current `y` and `x` positions::

            step_grid_rscan([det], y, -1, 1, 0.5, x, -1, 1, 0.5)
    """
    list_scan_args = _make_step_scan_args(args, grid=True)
    md = _make_step_scan_md(
        "step_grid_rscan", detectors, args, md, snake_axes=snake_axes
    )
    yield from bp.rel_list_grid_scan(
        detectors, *list_scan_args, snake_axes=snake_axes, md=md
    )
