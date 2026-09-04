from collections.abc import Iterable, Sequence
from typing import Annotated as A
from typing import Any

import bluesky.plans as bp
from bluesky.protocols import Movable
from pydantic import Field, NonNegativeFloat, validate_call

from dodal.common import MsgGenerator
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator
from dodal.plans.scans.annotations import (
    DetectorsA,
    MovableListOfPoints,
    MovableListOfPointsA,
    MovableStartStep,
    MovableStartStop,
    MovableStartStopA,
    MovableStartStopNum,
    MovableStartStopNumA,
    MovableStartStopStep,
    MovableStartStopStepA,
)
from dodal.plans.scans.utils import (
    flatten,
    make_step_grid_scan_args_and_shape,
    make_step_scan_args_and_shape,
)

"""This module wraps plan(s) from bluesky.plans so they are compatible with blueapi.
Required decorators are installed on plan import.
https://github.com/DiamondLightSource/blueapi/issues/474

Non-serialisable fields are ignored when they are optional.
https://github.com/DiamondLightSource/blueapi/issues/711

Using *args in plans is currently not supported.
https://github.com/DiamondLightSource/blueapi/issues/1450

We may also need other adjustments for UI purposes, e.g.
    - Forcing uniqueness or orderedness of Readables.
    - Limits and metadata (e.g. units).
"""


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
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
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Reads from a number of devices.

    Wraps bluesky.plans.count(det, num, delay, md=metadata) exposing only serializable
    parameters and metadata.
    """
    if isinstance(delay, Sequence):
        assert len(delay) == num - 1, (
            f"Number of delays given must be {num - 1}: was given {len(delay)}"
        )
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.count(tuple(detectors), num, delay=delay, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def num_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStop,
    *extra_axes: MovableStartStopA,
    num: int,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by number of points along scan trajector(y/ies). Wraps
    bluesky.plans.scan(det, *args, num, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)

    yield from bp.scan(
        detectors, *trajectory, *flatten(extra_axes), num=num, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopNum,
    *extra_trajectories: MovableStartStopNumA,
    snake_axes: Iterable[Movable] | bool = False,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent multi-motor trajectories.

    The scan is defined by number of points along scan trajectories. Snakes all fast
    axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata).
    """
    yield from bp.grid_scan(
        detectors,
        *trajectory,
        *flatten(extra_trajectories),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
def num_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStop,
    *extra_trajectories: MovableStartStopA,
    num: int,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position(s).

    The scan is defined by number of points along scan trajector(y/ies). Wraps
    bluesky.plans.rel_scan(det, *args, num, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)

    yield from bp.rel_scan(
        detectors, *trajectory, *flatten(extra_trajectories), num=num, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopNum,
    *extra_trajectories: MovableStartStopNumA,
    snake_axes: list | bool = True,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories, relative to current positions.

    The scan is defined by number of points along scan trajectories. Snakes all fast
    axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata).
    """
    yield from bp.rel_grid_scan(
        detectors,
        *trajectory,
        *flatten(extra_trajectories),
        snake_axes=snake_axes,
        md=metadata,
    )


def _make_list_scan_shape(
    params: Sequence[MovableListOfPoints], grid: bool
) -> tuple[int, ...]:
    shape = []
    for param in params:
        points = param[1]
        # List arg must all be same size. If list missing or not same size, this will
        # be validated by bp.list_scan.
        dim = len(points)
        shape.append(dim)
        if not grid:
            break

    return tuple(shape)


@validate_call(config={"arbitrary_types_allowed": True})
def list_scan(
    detectors: DetectorsA,
    trajectory: MovableListOfPoints,
    *extra_trajectories: MovableListOfPointsA,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.list_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=False
    )
    # typing is wrong for list scan.
    yield from bp.list_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),  # type: ignore
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableListOfPoints,
    *extra_trajectories: MovableListOfPointsA,
    snake_axes: bool = False,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories.

    The scan is defined by providing a list of points for each scan trajectory. Snakes
    all fast axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.list_grid_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=True
    )
    yield from bp.list_grid_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
def list_rscan(
    detectors: DetectorsA,
    trajectory: MovableListOfPoints,
    *extra_trajectories: MovableListOfPointsA,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position.

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=False
    )
    yield from bp.rel_list_scan(
        detectors, *flatten([trajectory, *extra_trajectories]), md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableListOfPoints,
    *extra_trajectories: MovableListOfPointsA,
    snake_axes: bool = True,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories, relative to current positions.

    The scan is defined by providing a list of points for each scan trajectory. Snakes
    all fast axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.rel_list_grid_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(
        [trajectory, *extra_trajectories], grid=True
    )
    yield from bp.rel_list_grid_scan(
        detectors,
        *flatten([trajectory, *extra_trajectories]),
        snake_axes=snake_axes,
        md=metadata,
    )


@validate_call(config={"arbitrary_types_allowed": True})
def step_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStep,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_scan_args_and_shape(trajectory, extra_trajectories)
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.list_scan(detectors, *flatten(args), md=metadata)  # type: ignore


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_scan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStepA,
    *extra_trajectories: MovableStartStopStepA,
    snake_axes: bool = True,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata). Snakes all fast axes by
    default (all axes but the first axis provided).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_grid_scan_args_and_shape([trajectory, *extra_trajectories])
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.list_grid_scan(
        detectors, *flatten(args), snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def step_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStep,
    *extra_trajectories: MovableStartStep,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_scan_args_and_shape(trajectory, extra_trajectories)
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.rel_list_scan(detectors, *flatten(args), md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_rscan(
    detectors: DetectorsA,
    trajectory: MovableStartStopStep,
    *extra_trajectories: MovableStartStopStepA,
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata). Snakes all fast axes by
    default (all axes but the first axis provided).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = make_step_grid_scan_args_and_shape([trajectory, *extra_trajectories])
    metadata = metadata or {}
    metadata["shape"] = shape
    yield from bp.rel_list_grid_scan(
        detectors, *flatten(args), snake_axes=snake_axes, md=metadata
    )
