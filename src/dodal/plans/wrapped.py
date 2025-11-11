from collections.abc import Sequence
from typing import Annotated, Any

import bluesky.plans as bp
from bluesky.protocols import Readable
from pydantic import Field, NonNegativeFloat, validate_call

from dodal.common import MsgGenerator
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator

"""This module wraps plan(s) from bluesky.plans until required handling for them is
moved into bluesky or better handled in downstream services.

Required decorators are installed on plan import
https://github.com/DiamondLightSource/blueapi/issues/474

Non-serialisable fields are ignored when they are optional
https://github.com/DiamondLightSource/blueapi/issues/711

We may also need other adjustments for UI purposes, e.g.
Forcing uniqueness or orderedness of Readables
Limits and metadata (e.g. units)
"""


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def count(
    detectors: Annotated[
        set[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    num: Annotated[int, Field(description="Number of frames to collect", ge=1)] = 1,
    delay: Annotated[
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
    parameters and metadata."""
    if isinstance(delay, Sequence):
        assert len(delay) == num - 1, (
            f"Number of delays given must be {num - 1}: was given {len(delay)}"
        )
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.count(tuple(detectors), num, delay=delay, md=metadata)


def scan(
    detectors: Annotated[
        set[Readable] | list[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    args: Annotated[
        tuple,
        Field(
            description="For one or more dimensions, 'motor1, start1, stop1, ..., "
            "motorN, startN, stopN'. Motors can be any 'settable' object (motor, "
            "temp controller, etc.)"
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory.
    Wraps bluesky.plans.scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.scan(tuple(detectors), *args, num=num, md=metadata)


def rel_scan(
    detectors: Annotated[
        set[Readable] | list[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    args: Annotated[
        tuple,
        Field(
            description="For one or more dimensions, 'motor1, start1, stop1, ..., "
            "motorN, startN, stopN'. Motors can be any 'settable' object (motor, "
            "temp controller, etc.)"
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory, relative to current position.
    Wraps bluesky.plans.rel_scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.rel_scan(tuple(detectors), *args, num=num, md=metadata)


def grid_scan(
    detectors: Annotated[
        set[Readable] | list[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    args: Annotated[
        tuple,
        Field(
            description="Patterend like (motor1, start1, stop1, num1, ..., motorN, "
            "startN, stopN, numN). The first motor is the 'slowest', the outer loop. "
            "For all motors except the first motor, there is a 'snake' argument: a"
            "boolean indicating whether to follow snake-like, winding trajectory or a"
            "simple left to right."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh; each motor is on an independent trajectory.
    Wraps bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    yield from bp.grid_scan(tuple(detectors), *args, snake_axes=snake_axes, md=metadata)


def rel_grid_scan(
    detectors: Annotated[
        set[Readable] | list[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    args: Annotated[
        tuple,
        Field(
            description="Patterend like (motor1, start1, stop1, num1, ..., motorN, "
            "startN, stopN, numN). The first motor is the 'slowest', the outer loop. "
            "For all motors except the first motor, there is a 'snake' argument: a"
            "boolean indicating whether to follow snake-like, winding trajectory or a"
            "simple left to right."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh relative to current position.
    Wraps bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    yield from bp.rel_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
