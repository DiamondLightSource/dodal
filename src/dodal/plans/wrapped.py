from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Any

import bluesky.plans as bp
import numpy as np
from bluesky.protocols import Movable, Readable
from ophyd_async.core import AsyncReadable
from pydantic import Field, NonNegativeFloat, validate_call

from dodal.common import MsgGenerator
from dodal.devices.motors import Motor
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator

"""This module wraps plan(s) from bluesky.plans until required handling for them is
moved into bluesky or better handled in downstream services.

Required decorators are installed on plan import
https://github.com/DiamondLightSource/blueapi/issues/474

Non-serialisable fields are ignored when they are optional
https://github.com/DiamondLightSource/blueapi/issues/711

We may also need other adjustments for UI purposes, e.g.
    - Forcing uniqueness or orderedness of Readables.
    - Limits and metadata (e.g. units).
"""


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def count(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
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
    parameters and metadata.
    """
    if isinstance(delay, Sequence):
        assert len(delay) == num - 1, (
            f"Number of delays given must be {num - 1}: was given {len(delay)}"
        )
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.count(tuple(detectors), num, delay=delay, md=metadata)


def _make_num_scan_args(params: dict[Movable | Motor, list[float | int]]):
    shape = []
    for param in params:
        if len(params[param]) == 3:
            shape.append(params[param][-1])
    args = []
    for param, movable_num in zip(params, range(len(params)), strict=True):
        args.append(param)
        if movable_num == 0 and len(shape) == 1:
            params[param].pop()
        args.extend(params[param])
    return args, shape


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def num_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For concurrent "
            "trajectories, provide '{movable1: [start1, stop1, num], movable2: [start2,"
            "stop2], ... , movableN: [startN, stopN]}'. For independent trajectories,"
            "provide '{movable1: [start1, stop1, num1], ... , movableN: [startN, stopN,"
            "numN]}'."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over concurrent or independent multi-motor trajectories.
    Wraps bluesky.plans.scan(det, *args, num, md=metadata) and
    bluesky.plans.grid_scan(det, *args, md=metadata)"""
    args, shape = _make_num_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.scan(tuple(detectors), *args, num=shape[0], md=metadata)
    elif len(shape) > 1:
        yield from bp.grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def num_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For concurrent "
            "trajectories, provide '{movable1: [start1, stop1, num], movable2: [start2,"
            "stop2], ... , movableN: [startN, stopN]}'. For independent trajectories,"
            "provide '{movable1: [start1, stop1, num1], ... , movableN: [startN, stopN,"
            "numN]}'."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over concurrent or independent trajectories relative to current position.
    Wraps bluesky.plans.rel_scan(det, *args, num, md=metadata) and
    bluesky.plans.rel_grid_scan(det, *args, md=metadata)"""
    args, shape = _make_num_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.rel_scan(tuple(detectors), *args, num=shape[0], md=metadata)
    elif len(shape) > 1:
        yield from bp.rel_grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )


def _make_list_scan_args(params: dict[Movable | Motor, list[float | int]], grid: bool):
    shape = []
    args = []
    for param, num in zip(params, range(len(params)), strict=True):
        if num == 0:
            shape.append(len(params[param]))
        elif num >= 1 and grid:
            shape.append(len(params[param]))
        args.append(param)
        args.append(params[param])
    return args, shape


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def list_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For all trajectories, "
            "provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, "
            "...]}'."
        ),
    ],
    grid: bool = False,
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over concurrent or independent trajectories relative to current position.
    To scan over concurrent trajectories, grid = False, and independent trajectories,
    grid = True.
    Wraps bluesky.plans.list_scan(det, *args, num, md=metadata) and
    bluesky.plans.list_grid_scan(det, *args, md=metadata)"""
    args, shape = _make_list_scan_args(params=params, grid=grid)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.list_scan(tuple(detectors), *args, md=metadata)
    elif len(shape) > 1:
        yield from bp.list_grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def list_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For all trajectories, "
            "provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, "
            "...]}'."
        ),
    ],
    grid: bool = False,
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over concurrent or independent trajectories relative to current position.
    To scan over concurrent trajectories, grid = False, and independent trajectories,
    grid = True.
    Wraps bluesky.plans.rel_list_scan(det, *args, num, md=metadata) and
    bluesky.plans.rel_list_grid_scan(det, *args, md=metadata)"""
    args, shape = _make_list_scan_args(params=params, grid=grid)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)
    elif len(shape) > 1:
        yield from bp.rel_list_grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )


def _make_stepped_list(
    params: list[Any] | Sequence[Any],
    num: int | None = None,
):
    def round_list_elements(stepped_list, step):
        d = Decimal(str(step))
        exponent = d.as_tuple().exponent
        decimal_places = -exponent  # type: ignore
        return np.round(stepped_list, decimals=decimal_places).tolist()

    start = params[0]
    if len(params) == 3:
        stop = params[1]
        step = params[2]
        if abs(step) > abs(stop - start):
            step = stop - start
        step = abs(step) * np.sign(stop - start)
        stepped_list = np.arange(start=start, stop=stop, step=step).tolist()
        if abs((stepped_list[-1] + step) - stop) <= abs(step * 0.01):
            stepped_list.append(stepped_list[-1] + step)
        rounded_stepped_list = round_list_elements(stepped_list=stepped_list, step=step)
    elif len(params) == 2 and num:
        step = params[1]
        stepped_list = [start + (n * step) for n in range(num)]
        rounded_stepped_list = round_list_elements(stepped_list=stepped_list, step=step)
    else:
        raise ValueError(
            f"You provided {len(params)}, rather than 3, or 2 and number of points."
        )

    return rounded_stepped_list, len(rounded_stepped_list)


def _make_step_scan_args(params: dict[Movable | Motor, list[float | int]]):
    args = []
    shape = []
    stepped_list_length = None
    for param, movable_num in zip(params, range(len(params)), strict=True):
        if movable_num == 0:
            if len(params[param]) == 3:
                stepped_list, stepped_list_length = _make_stepped_list(
                    params=params[param]
                )
                args.append(param)
                args.append(stepped_list)
                shape.append(stepped_list_length)
            else:
                raise ValueError(
                    f"You provided {len(params[param])} parameters, rather than 3."
                )
        elif movable_num >= 1:
            if len(params[param]) == 2:
                stepped_list, stepped_list_length = _make_stepped_list(
                    params=params[param], num=stepped_list_length
                )
                args.append(param)
                args.append(stepped_list)
            elif len(params[param]) == 3:
                stepped_list, stepped_list_length = _make_stepped_list(
                    params=params[param]
                )
                args.append(param)
                args.append(stepped_list)
                shape.append(stepped_list_length)
            else:
                raise ValueError(
                    f"You provided {len(params[param])} parameters, rather than 2 or 3."
                )
    if (len(args) / len(shape)) not in [2, len(args)]:
        raise ValueError(
            "Incorrect number of parameters, unsure if scan is concurrent/independent."
        )

    return args, shape


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def step_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For concurrent "
            "trajectories, provide '{movable1: [start1, stop1, step1], movable2: "
            "[start2, step2], ... , movableN: [startN, stepN]}'. For independent "
            "trajectories, provide '{movable1: [start1, stop1, step1], ... , movableN: "
            "[startN, stopN, stepN]}'."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over multi-motor trajectories with specified step size.
    Generates lists of points for each trajectory for
    bluesky.plans.list_scan(det, *args, num, md=metadata) and
    bluesky.plans.list_grid_scan(det, *args, md=metadata)."""
    args, shape = _make_step_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.list_scan(tuple(detectors), *args, md=metadata)
    elif len(shape) > 1:
        yield from bp.list_grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def step_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: paramater' keys. For concurrent "
            "trajectories, provide '{movable1: [start1, stop1, step1], movable2: "
            "[start2, step2], ... , movableN: [startN, stepN]}'. For independent "
            "trajectories, provide '{movable1: [start1, stop1, step1], ... , movableN: "
            "[startN, stopN, stepN]}'."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over multi-motor trajectories with specified step size.
    Generates lists of points for each trajectory for
    bluesky.plans.list_scan(det, *args, num, md=metadata) and
    bluesky.plans.list_grid_scan(det, *args, md=metadata)."""
    args, shape = _make_step_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    if len(shape) == 1:
        yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)
    elif len(shape) > 1:
        yield from bp.rel_list_grid_scan(
            tuple(detectors), *args, snake_axes=snake_axes, md=metadata
        )
