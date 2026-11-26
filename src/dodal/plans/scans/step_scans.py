import math
from collections.abc import Callable, Sequence
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
    """Return the most decimal places of any of the values e.g. (1, 0.5, 0.25) -> 2."""
    return max(0, *(-int(Decimal(str(v)).as_tuple().exponent) for v in values))


def _positions(start: float, step: float, num: int, decimal_places: int) -> list[float]:
    """Return `num` positions from `start` in increments of `step`, rounded to remove
    floating point error, e.g. 0.30000000000000004 -> 0.3.
    """
    return np.round(start + step * np.arange(num), decimal_places).tolist()


def _make_stepped_list_step(start: float, stop: float, step: float) -> list[float]:
    """Return positions from `start` to `stop` in increments of `step`.

    The sign of `step` is ignored, it always moves from `start` towards `stop`. A step
    larger than the range gives just `start` and `stop`. `stop` is only included if it
    is reached by a whole number of steps, to within 5% of a step.
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
    """Return `num` positions from `start` in increments of `step`."""
    return _positions(start, step, num, _decimal_places(start, step))


def _group_args_by_movable(
    args: Sequence[StepScanArg],
) -> list[tuple[NamedMovable, list[float | int]]]:
    """Split a flat sequence of arguments into (movable, [numbers...]) groups.

    A new group is started every time a movable is encountered; all numbers that follow
    it, up to the next movable, belong to that group. e.g.
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


def _make_step_scan_args(
    args: Sequence[StepScanArg], grid: bool
) -> tuple[list[Any], list[int]]:
    """Convert flat step scan arguments into bluesky list scan arguments.

    Args:
        args: Flat sequence of movables and numbers, as passed to a step scan.
        grid: If True, every movable must be given `start, stop, step` and moves
            independently (grid). If False, only the first movable is given
            `start, stop, step` and every following movable is given `start, step`
            and moves concurrently with it, taking the same number of points.

    Returns:
        A tuple of (args for `bluesky.plans.list_scan`-style plans, i.e.
        `[movable1, positions1, movable2, positions2, ...]`, and the shape of the
        scan).
    """
    list_scan_args: list[Any] = []
    shape: list[int] = []
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
            shape.append(len(positions))
        else:
            positions = _make_stepped_list_num(*params, num=shape[0])
        list_scan_args += [movable, positions]

    return list_scan_args, shape


def _make_step_scan_md(
    plan_name: str,
    detectors: Sequence[Readable],
    args: Sequence[StepScanArg],
    shape: list[int],
    metadata: CustomPlanMetadata | None,
    **plan_args: Any,
) -> CustomPlanMetadata:
    """Create the run start metadata for a step scan.

    Args:
        plan_name: Name of the step scan plan.
        detectors: Detectors passed to the plan.
        args: Flat movable and number arguments passed to the plan.
        shape: Number of points along each dimension of the scan.
        metadata: User supplied metadata, merged in last.
        **plan_args: Any further plan arguments to record e.g. `snake_axes`.

    Returns:
        Metadata to pass as `md` to the bluesky plan.
    """
    return {
        "plan_name": plan_name,
        "plan_args": {
            "detectors": list(map(repr, detectors)),
            "args": [repr(a) if isinstance(a, NamedMovable) else a for a in args],
            **plan_args,
        },
        "detectors": [det.name for det in detectors],
        "shape": shape,
        **(metadata or {}),
    }


def _run_step_scan(
    plan: Callable[..., MsgGenerator],
    plan_name: str,
    detectors: Sequence[Readable],
    args: Sequence[StepScanArg],
    metadata: CustomPlanMetadata | None,
    *,
    grid: bool,
    **plan_kwargs: Any,
) -> MsgGenerator:
    """Calculate the positions for a step scan and run it with a bluesky list plan.

    `plan_kwargs` (e.g. `snake_axes`) are passed to `plan` and recorded in the
    `plan_args` metadata.
    """
    list_scan_args, shape = _make_step_scan_args(args, grid=grid)
    md = _make_step_scan_md(plan_name, detectors, args, shape, metadata, **plan_kwargs)
    yield from plan(detectors, *list_scan_args, md=md, **plan_kwargs)


def step_scan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more movables concurrently, defined by a step size.

    The first movable is given a start, stop and step, which defines the number of
    points in the scan. Any further movables are given a start and step only, and move
    concurrently with the first, taking the same number of points. The positions for
    every movable are calculated up front and passed to `bluesky.plans.list_scan`.

    Args:
        detectors: Readable devices, a reading is taken of each at every point.
        *args: A flat sequence describing each axis, in the form
            `movable1, start1, stop1, step1, movable2, start2, step2, ...,
            movableN, startN, stepN`.
        metadata: Additional metadata to add to the run start document. This takes
            priority over the metadata generated by the plan.

    Examples:
        Move `x` from 0 to 10 in steps of 1 (11 points), reading `det` at each::

            step_scan([det], x, 0, 10, 1)

        Move `x` from 0 to 10 in steps of 1 and, at the same time, `y` from 5 in
        steps of 0.5 (11 points, `y` ending at 10)::

            step_scan([det], x, 0, 10, 1, y, 5, 0.5)

    Raises:
        ValueError: If no movable is given, the first argument after `detectors` is
            not a movable, the wrong number of parameters are given for a movable or
            the start and stop of the first movable are equal.
        TypeError: If an argument after `detectors` is neither a movable nor a
            number.
    """
    yield from _run_step_scan(
        bp.list_scan, "step_scan", detectors, args, metadata, grid=False
    )


def step_rscan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more movables concurrently, defined by a step size, relative to
    their current positions.

    Identical to `step_scan`, except every start and stop is relative to the
    movable's position at the start of the scan, and every movable is returned to that
    position once the scan finishes. Uses `bluesky.plans.rel_list_scan`.

    Args:
        detectors: Readable devices, a reading is taken of each at every point.
        *args: A flat sequence describing each axis, in the form
            `movable1, start1, stop1, step1, movable2, start2, step2, ...,
            movableN, startN, stepN`, all relative to the current positions.
        metadata: Additional metadata to add to the run start document. This takes
            priority over the metadata generated by the plan.

    Examples:
        Move `x` from 1 below to 1 above its current position in steps of 0.1
        (21 points)::

            step_rscan([det], x, -1, 1, 0.1)

        As above, while also moving `y` from its current position in steps of 0.05::

            step_rscan([det], x, -1, 1, 0.1, y, 0, 0.05)

    Raises:
        ValueError: If no movable is given, the first argument after `detectors` is
            not a movable, the wrong number of parameters are given for a movable or
            the start and stop of the first movable are equal.
        TypeError: If an argument after `detectors` is neither a movable nor a
            number.
    """
    yield from _run_step_scan(
        bp.rel_list_scan, "step_rscan", detectors, args, metadata, grid=False
    )


def step_grid_scan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan a grid of movables moving independently, each defined by a step size.

    Every movable is given a start, stop and step. The first movable is the slowest
    (outermost) axis and the last is the fastest (innermost). The positions for every
    movable are calculated up front and passed to `bluesky.plans.list_grid_scan`.

    Args:
        detectors: Readable devices, a reading is taken of each at every point.
        *args: A flat sequence describing each axis, in the form
            `movable1, start1, stop1, step1, ..., movableN, startN, stopN, stepN`.
        snake_axes: If True (default), every axis except the first (slowest) axis
            reverses direction on alternate passes rather than returning to its
            start. Snaking individual axes is not currently supported.
        metadata: Additional metadata to add to the run start document. This takes
            priority over the metadata generated by the plan.

    Examples:
        A 2D grid, `y` from 0 to 2 in steps of 0.5 (5 rows) and `x` from 0 to 1 in
        steps of 0.25 (5 columns), 25 points in total::

            step_grid_scan([det], y, 0, 2, 0.5, x, 0, 1, 0.25)

        The same grid without snaking, so `x` always moves from 0 to 1::

            step_grid_scan([det], y, 0, 2, 0.5, x, 0, 1, 0.25, snake_axes=False)

    Raises:
        ValueError: If no movable is given, the first argument after `detectors` is
            not a movable, any movable is not given exactly 3 parameters or any
            start and stop are equal.
        TypeError: If an argument after `detectors` is neither a movable nor a
            number.
    """
    yield from _run_step_scan(
        bp.list_grid_scan,
        "step_grid_scan",
        detectors,
        args,
        metadata,
        grid=True,
        snake_axes=snake_axes,
    )


def step_grid_rscan(
    detectors: Sequence[Readable],
    *args: StepScanArg,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan a grid of movables moving independently, each defined by a step size,
    relative to their current positions.

    Identical to `step_grid_scan`, except every start and stop is relative to the
    movable's position at the start of the scan, and every movable is returned to that
    position once the scan finishes. Uses `bluesky.plans.rel_list_grid_scan`.

    Args:
        detectors: Readable devices, a reading is taken of each at every point.
        *args: A flat sequence describing each axis, in the form
            `movable1, start1, stop1, step1, ..., movableN, startN, stopN, stepN`,
            all relative to the current positions.
        snake_axes: If True (default), every axis except the first (slowest) axis
            reverses direction on alternate passes rather than returning to its
            start. Snaking individual axes is not currently supported.
        metadata: Additional metadata to add to the run start document. This takes
            priority over the metadata generated by the plan.

    Examples:
        A 2D grid of 1 either side of the current `y` and `x` positions, in steps
        of 0.5 (5 x 5 = 25 points)::

            step_grid_rscan([det], y, -1, 1, 0.5, x, -1, 1, 0.5)

    Raises:
        ValueError: If no movable is given, the first argument after `detectors` is
            not a movable, any movable is not given exactly 3 parameters or any
            start and stop are equal.
        TypeError: If an argument after `detectors` is neither a movable nor a
            number.
    """
    yield from _run_step_scan(
        bp.rel_list_grid_scan,
        "step_grid_rscan",
        detectors,
        args,
        metadata,
        grid=True,
        snake_axes=snake_axes,
    )
