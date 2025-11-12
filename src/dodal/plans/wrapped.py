import itertools
from collections.abc import Sequence
from typing import Annotated, Any

import bluesky.plans as bp
from bluesky.protocols import Movable, Readable
from ophyd_async.core import AsyncReadable
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
        set[Readable | AsyncReadable],
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


def _make_args(movables, params, num_params):
    movables_len = len(movables)
    params_len = len(params)
    if params_len % movables_len != 0 or params_len % num_params != 0:
        raise ValueError(f"params must contain {num_params} values for each movable")

    args = []
    it = iter(params)
    param_chunks = iter(lambda: tuple(itertools.islice(it, num_params)), ())
    for movable, param_chunk in zip(movables, param_chunks, strict=False):
        args.append(movable)
        args.extend(param_chunk)
    return args


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def scan(
    detectors: Annotated[
        set[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movables: Annotated[
        list[Movable], Field(description="One or more movable to move during the scan.")
    ],
    params: Annotated[
        list[float],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movables`."
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory.
    Wraps bluesky.plans.scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    args = _make_args(movables=movables, params=params, num_params=2)
    yield from bp.scan(tuple(detectors), *args, num=num, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def rel_scan(
    detectors: Annotated[
        set[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movables: Annotated[
        list[Movable], Field(description="One or more movable to move during the scan.")
    ],
    params: Annotated[
        list[float],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movables`."
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory, relative to current position.
    Wraps bluesky.plans.rel_scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    args = _make_args(movables=movables, params=params, num_params=2)
    yield from bp.rel_scan(tuple(detectors), *args, num=num, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def grid_scan(
    detectors: Annotated[
        set[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movables: Annotated[
        list[Movable], Field(description="One or more movable to move during the scan.")
    ],
    params: Annotated[
        list[float | int],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movables`."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh; each motor is on an independent trajectory.
    Wraps bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    args = _make_args(movables=movables, params=params, num_params=3)
    yield from bp.grid_scan(tuple(detectors), *args, snake_axes=snake_axes, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def rel_grid_scan(
    detectors: Annotated[
        set[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movables: Annotated[
        list[Movable], Field(description="One or more movable to move during the scan.")
    ],
    params: Annotated[
        list[float | int],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movables`."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh relative to current position.
    Wraps bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    args = _make_args(movables=movables, params=params, num_params=3)
    yield from bp.rel_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
