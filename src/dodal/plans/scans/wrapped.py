from collections.abc import Iterable, Sequence
from typing import Annotated as A

import bluesky.plans as bp
from bluesky.protocols import Movable
from bluesky.utils import CustomPlanMetadata, plan
from pydantic import Field, NonNegativeFloat, validate_call

from dodal.common import MsgGenerator
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator
from dodal.plans.scans.annotations import (
    DetectorsA,
    MovableListOfPointsA,
    MovableStartStepA,
    MovableStartStopA,
    MovableStartStopNumA,
    MovableStartStopStepA,
)
from dodal.plans.scans.utils import (
    flatten,
    make_list_scan_shape,
    make_step_grid_scan_args_and_shape,
    make_step_scan_args_and_shape,
)

"""This module wraps plan(s) from bluesky.plans so they are compatible with blueapi.
Required decorators are installed on plan import.
https://github.com/DiamondLightSource/blueapi/issues/474

Non-serialisable fields are ignored when they are optional.
https://github.com/DiamondLightSource/blueapi/issues/711

We may also need other adjustments for UI purposes, e.g.
    - Forcing uniqueness or orderedness of Readables.
    - Limits and metadata (e.g. units).
"""


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
@plan
def count(
    detectors: DetectorsA,
    num: A[int, Field(description="Number of frames to collect", ge=1)] = 1,
    delay: A[
        NonNegativeFloat | Sequence[NonNegativeFloat],
        Field(
            description="Delay between readings: if tuple, len(delay) == num - 1 and \
            the delays are between each point, if value or None is the delay for every \
            gap",
            json_schema_extra={"units": "s"},
        ),
    ] = 0.0,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Read from a number of devices.

    Args:
        detectors: Devices to trigger and read.
        num: Number of readings to collect.
        delay: Delay between readings in seconds. A single value applies to
            every gap. A sequence specifies an individual delay for each gap
            and must contain ``num - 1`` values.
        metadata: Additional metadata to include in the run.

    Examples:
        Collect 10 readings with a 1-second delay between each reading::

            count([detector], num=10, delay=1.0)

        Use a different delay for each gap::

            count([detector], num=3, delay=[0.5, 1.0])

    Wraps:
        ``bluesky.plans.count(det, num, delay, md=metadata)``.
    """
    if isinstance(delay, Sequence):
        assert len(delay) == num - 1, (
            f"Number of delays given must be {num - 1}: was given {len(delay)}"
        )
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.count(tuple(detectors), num, delay=delay, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def num_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopA,
    *extra_trajectories: MovableStartStopA,
    num: int,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors over a specified range.

    The scan is defined by the number of points along each trajectory.
    All trajectories are scanned concurrently.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, start position,
            and stop position.
        *extra_trajectories: Additional trajectories to scan concurrently.
        num: Number of points in the scan.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from 0 to 10 in 11 points::

            num_scan([detector], (motor, 0, 10), num=11)

        Scan two motors concurrently::

            num_scan([detector], (x_motor, 0, 10), (y_motor, 5, 15), num=11)

    Wraps:
        ``bluesky.plans.scan(det, *args, num, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)

    yield from bp.scan(
        detectors, *trajectory, *flatten(extra_trajectories), num=num, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def num_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopNumA,
    *extra_trajectories: MovableStartStopNumA,
    snake_axes: Iterable[Movable] | bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent multi-motor trajectories.

    Each trajectory is defined by a movable, start position, stop position,
    and number of points. The trajectories are scanned independently to
    produce a grid. By default, all axes except the first axis are snaked.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, start position,
            stop position, and number of points.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Axes to snake, or ``True`` to snake all axes except the
            first axis. ``False`` disables snaking.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from 0 to 10 using 11 points::

            num_grid_scan([detector], (x_motor, 0, 10, 11))

        Scan two motors over a 2D grid::

            num_grid_scan([detector], (x_motor, 0, 10, 11), (y_motor, 0, 5, 6))

    Wraps:
        ``bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata)``.
    """
    yield from bp.grid_scan(
        detectors,
        *trajectory,
        *flatten(extra_trajectories),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def num_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopA,
    *extra_trajectories: MovableStartStopA,
    num: int,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors relative to their current positions.

    Each trajectory defines a relative start and stop position. The scan is
    performed using the specified number of points, with all trajectories
    scanned concurrently.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, relative start
            position, and relative stop position.
        *extra_trajectories: Additional trajectories to scan concurrently.
        num: Number of points in the scan.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from its current position to 10 units above it,
        using 11 points::

            num_rscan([detector], (x_motor, 0, 10), num=11)

        Scan two motors concurrently relative to their current positions::

            num_rscan([detector], (x_motor, 0, 10), (y_motor, -5, 5), num=11)

    Wraps:
        ``bluesky.plans.rel_scan(det, *args, num, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.rel_scan(
        detectors, *trajectory, *flatten(extra_trajectories), num=num, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def num_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopNumA,
    *extra_trajectories: MovableStartStopNumA,
    snake_axes: list | bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent trajectories relative to current positions.

    Each trajectory is defined by a movable, relative start position, relative
    stop position, and number of points. The trajectories are scanned
    independently to produce a grid. By default, all axes except the first
    axis are snaked.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, relative start
            position, relative stop position, and number of points.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Axes to snake, or ``True`` to snake all axes except the
            first axis. ``False`` disables snaking.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from its current position to 10 units above it,
        using 11 points::

            num_grid_rscan([detector], (x_motor, 0, 10, 11))

        Scan two motors over a 2D grid relative to their current positions::

            num_grid_rscan([detector], (x_motor, 0, 10, 11), (y_motor, -5, 5, 11))

    Wraps:
        ``bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata)``.
    """
    yield from bp.rel_grid_scan(
        detectors,
        *trajectory,
        *flatten(extra_trajectories),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def list_scan(
    detectors: DetectorsA,
    trajectory: MovableListOfPointsA,
    *extra_trajectories: MovableListOfPointsA,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors through specified lists of positions.

    Each trajectory is defined by a movable and a list of positions. All
    trajectories are scanned concurrently, with one point from each
    trajectory used at each scan step.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable and a list of
            positions.
        *extra_trajectories: Additional trajectories to scan concurrently.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan a motor through a list of positions::

            list_scan([detector], (x_motor, [0, 1, 2, 3]))

        Scan two motors concurrently through corresponding lists of
        positions::

            list_scan([detector], (x_motor, [0, 1, 2]), (y_motor, [10, 20, 30]))

    Wraps:
        ``bluesky.plans.list_scan(det, *args, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=False
    )
    # typing is wrong for list scan.
    yield from bp.list_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),  # type: ignore
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def list_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableListOfPointsA,
    *extra_trajectories: MovableListOfPointsA,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent trajectories through specified lists of positions.

    Each trajectory is defined by a movable and a list of positions. The
    trajectories are scanned independently to produce a grid. By default,
    snaking is disabled.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable and a list of
            positions.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Whether to snake the fast axes. ``False`` disables
            snaking.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor through a list of positions::

            list_grid_scan([detector], (x_motor, [0, 1, 2, 3]))

        Scan two motors over a 2D grid::

            list_grid_scan([detector], (x_motor, [0, 1, 2]), (y_motor, [10, 20, 30]))

    Wraps:
        ``bluesky.plans.list_grid_scan(det, *args, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=True
    )
    yield from bp.list_grid_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def list_rscan(
    detectors: DetectorsA,
    trajectory: MovableListOfPointsA,
    *extra_trajectories: MovableListOfPointsA,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors through relative positions.

    Each trajectory is defined by a movable and a list of positions relative
    to the motor's current position. All trajectories are scanned concurrently,
    with one point from each trajectory used at each scan step.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable and a list of
            relative positions.
        *extra_trajectories: Additional trajectories to scan concurrently.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan a motor through relative positions::

            list_rscan([detector], (x_motor, [0, 1, 2, 3]))

        Scan two motors concurrently through corresponding relative
        positions::

            list_rscan([detector], (x_motor, [0, 1, 2]), (y_motor, [-1, 0, 1]))

    Wraps:
        ``bluesky.plans.rel_list_scan(det, *args, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=False
    )
    yield from bp.rel_list_scan(
        detectors, *flatten([trajectory, *extra_trajectories]), md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def list_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableListOfPointsA,
    *extra_trajectories: MovableListOfPointsA,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent trajectories through relative positions.

    Each trajectory is defined by a movable and a list of positions relative
    to its current position. The trajectories are scanned independently to
    produce a grid. By default, all axes except the first axis are snaked.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable and a list of
            relative positions.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Whether to snake the fast axes. ``True`` enables snaking
            and ``False`` disables it.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor through relative positions::

            list_grid_rscan([detector], (x_motor, [0, 1, 2, 3]))

        Scan two motors over a 2D grid relative to their current positions::

            list_grid_rscan([detector], (x_motor, [0, 1, 2]), (y_motor, [-1, 0, 1]))

    Wraps:
        ``bluesky.plans.rel_list_grid_scan(det, *args, md=metadata)``.
    """
    metadata = metadata or {}
    metadata["shape"] = make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=True
    )
    yield from bp.rel_list_grid_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def step_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStepA,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors using specified step sizes.

    The primary trajectory is defined by a movable, start position, stop
    position, and step size. Additional trajectories are defined by a
    movable, start position, and step size and contain the same number of
    points as the primary trajectory. All trajectories are scanned
    concurrently.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, start position,
            stop position, and step size.
        *extra_trajectories: Additional trajectories to scan concurrently,
            defined by a movable, start position, and step size.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from 0 to 10 in steps of 1::

            step_scan([detector], (x_motor, 0, 10, 1))

        Scan two motors concurrently, with the second motor starting at 5
        and using the same number of points as the primary trajectory::

            step_scan([detector], (x_motor, 0, 10, 1), (y_motor, 5, 0.5))

    Wraps:
        ``bluesky.plans.list_scan(det, *args, md=metadata)``.
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_scan_args_and_shape(trajectory, extra_trajectories)
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.list_scan(detectors, *flatten(args), md=metadata)  # type: ignore


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def step_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStopStepA,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent trajectories using specified step sizes.

    Each trajectory is defined by a movable, start position, stop position,
    and step size. The trajectories are scanned independently to produce a
    grid. By default, all axes except the first axis are snaked.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, start position,
            stop position, and step size.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Whether to snake the fast axes. ``True`` enables snaking
            and ``False`` disables it.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from 0 to 10 in steps of 1::

            step_grid_scan([detector], (x_motor, 0, 10, 1))

        Scan two motors over a 2D grid::

            step_grid_scan([detector], (x_motor, 0, 10, 1), (y_motor, 0, 5, 1))

    Wraps:
        ``bluesky.plans.list_grid_scan(det, *args, md=metadata)``.
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_grid_scan_args_and_shape([trajectory, *extra_trajectories])
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.list_grid_scan(
        detectors, *flatten(args), snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def step_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStepA,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan one or more motors using relative step sizes.

    The primary trajectory is defined by a movable, relative start position,
    relative stop position, and step size. Additional trajectories are defined
    by a movable, relative start position, and step size and contain the same
    number of points as the primary trajectory. All trajectories are scanned
    concurrently.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, relative start
            position, relative stop position, and step size.
        *extra_trajectories: Additional trajectories to scan concurrently,
            defined by a movable, relative start position, and step size.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from its current position to 10 units above it,
        in steps of 1::

            step_rscan([detector], (x_motor, 0, 10, 1))

        Scan two motors concurrently using relative positions::

            step_rscan([detector], (x_motor, 0, 10, 1), (y_motor, -5, 0.5))

    Wraps:
        ``bluesky.plans.rel_list_scan(det, *args, md=metadata)``.
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_scan_args_and_shape(trajectory, extra_trajectories)
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.rel_list_scan(detectors, *flatten(args), md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
@plan
def step_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStopStepA,
    snake_axes: bool = True,
    metadata: CustomPlanMetadata | None = None,
) -> MsgGenerator:
    """Scan independent trajectories using relative step sizes.

    Each trajectory is defined by a movable, relative start position, relative
    stop position, and step size. The trajectories are scanned independently
    to produce a grid. By default, all axes except the first axis are snaked.

    Args:
        detectors: Devices to trigger and read at each scan point.
        trajectory: Primary trajectory defined by a movable, relative start
            position, relative stop position, and step size.
        *extra_trajectories: Additional trajectories to include in the grid.
        snake_axes: Whether to snake the fast axes. ``True`` enables snaking
            and ``False`` disables it.
        metadata: Additional metadata to include in the run.

    Examples:
        Scan one motor from its current position to 10 units above it,
        in steps of 1::

            step_grid_rscan([detector], (x_motor, 0, 10, 1))

        Scan two motors over a 2D grid relative to their current positions::

            step_grid_rscan([detector], (x_motor, 0, 10, 1), (y_motor, 0, 5, 1))

    Wraps:
        ``bluesky.plans.rel_list_grid_scan(det, *args, md=metadata)``.
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_grid_scan_args_and_shape([trajectory, *extra_trajectories])
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.rel_list_grid_scan(
        detectors, *flatten(args), snake_axes=snake_axes, md=metadata
    )
