import itertools
from collections.abc import Sequence
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
Forcing uniqueness or orderedness of Readables
Limits and metadata (e.g. units)
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
    parameters and metadata."""
    if isinstance(delay, Sequence):
        assert len(delay) == num - 1, (
            f"Number of delays given must be {num - 1}: was given {len(delay)}"
        )
    metadata = metadata or {}
    metadata["shape"] = (num,)
    yield from bp.count(tuple(detectors), num, delay=delay, md=metadata)


def _make_args(
    movers: Sequence[Movable | Motor],
    params: list[Any] | Sequence[Any],
    num_params: int,
):
    movers_len = len(movers)
    params_len = len(params)
    args = []
    if params_len % movers_len == 0 and params_len % num_params == 0:
        it = iter(params)
        param_chunks = iter(lambda: tuple(itertools.islice(it, num_params)), ())
        for movable, param_chunk in zip(movers, param_chunks, strict=False):
            args.append(movable)
            args.extend(param_chunk)
    else:
        raise ValueError(f"params must contain {num_params} values for each movable")
    return args


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[float],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movers`."
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory.
    Wraps bluesky.plans.scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    args = _make_args(movers=movers, params=params, num_params=2)
    yield from bp.scan(tuple(detectors), *args, num=num, md=metadata)


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[float],
        Field(
            description="Start and stop points for each movable, 'start1, stop1, ...,"
            "startN, stopN' for every movable in `movers`."
        ),
    ],
    num: Annotated[int, Field(description="Number of points")],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory, relative to current position.
    Wraps bluesky.plans.rel_scan(det, *args, num, md=metadata)"""
    metadata = metadata or {}
    metadata["shape"] = (num,)
    args = _make_args(movers=movers, params=params, num_params=2)
    yield from bp.rel_scan(tuple(detectors), *args, num=num, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def grid_num_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        Sequence[float | int],
        Field(
            description="Start and stop and number of points for each movable, 'start1,"
            "stop1, num1, ..., startN, stopN, numN' for every movable in `movers`."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh; each motor is on an independent trajectory.
    Wraps bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=3)
    yield from bp.grid_scan(tuple(detectors), *args, snake_axes=snake_axes, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def grid_num_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        Sequence[float | int],
        Field(
            description="Start and stop and number of points for each movable, 'start1,"
            "stop1, num1, ..., startN, stopN, numN' for every movable in `movers`."
        ),
    ],
    snake_axes: list | bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over a mesh relative to current position.
    Wraps bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata)"""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=3)
    yield from bp.rel_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[list[Any]],
        Field(
            description="List of points for each movable, '[point1, point2, ..., ], "
            "[point1, point2, ...], ...' for every movable in `movers`."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one or more variables in steps simultaneously.
    Wraps bluesky.plans.list_scan(det, *args, md=metadata)."""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=1)
    yield from bp.list_scan(tuple(detectors), *args, md=metadata)


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[list[Any]],
        Field(
            description="List of points for each movable, '[point1, point2, ..., ], "
            "[point1, point2, ...], ...' for every movable in `movers`."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one or more variables simultaneously relative to current position.
    Wraps bluesky.plans.rel_list_scan(det, *args, md=metadata)."""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=1)
    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[list[Any]],
        Field(
            description="List of points for each movable, '[point1, point2, ..., ], "
            "[point1, point2, ...], ...' for every movable in `movers`."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one or more variables for each given point on independent trajectories.
    Wraps bluesky.plans.list_grid_scan(det, *args, md=metadata)."""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=1)
    yield from bp.list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[list[Any]],
        Field(
            description="List of points for each movable, '[point1, point2, ..., ], "
            "[point1, point2, ...], ...' for every movable in `movers`."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over some variables for each given point relative to current position.
    Wraps bluesky.plans.rel_list_grid_scan(det, *args, md=metadata)."""
    metadata = metadata or {}
    args = _make_args(movers=movers, params=params, num_params=1)
    yield from bp.rel_list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


def _make_stepped_list(
    params: list[Any] | Sequence[Any],
    num: int | None = None,
):
    start = params[0]
    if len(params) == 3:
        stop = params[1]
        step = params[2]
        stepped_list = np.arange(start=start, stop=stop, step=step).tolist()
        if abs((stepped_list[-1] + step) - stop) <= (step * 0.01):
            stepped_list.append(stepped_list[-1] + step)
    elif len(params) == 2 and num:
        step = params[1]
        stepped_list = [start + (n * step) for n in range(num)]
    else:
        stepped_list = []
    return stepped_list


def _make_concurrently_stepped_lists(
    movers_len: int,
    params: list[Any] | Sequence[Any],
):
    # separate out the first three elements
    # separate the rest of the elements into chunks of two
    stepped_lists = []
    params_len = len(params)
    if movers_len == 1 and params_len == 3:
        stepped_lists.append(_make_stepped_list(params))
    elif movers_len > 1 and (params_len - 3) % 2 == 0:
        leader_params = params[:3]
        follower_params = params[3:]
        stepped_lists.append(_make_stepped_list(leader_params))
        num = len(stepped_lists[0])
        it = iter(follower_params)
        param_chunks = iter(lambda: tuple(itertools.islice(it, 2)), ())
        for param_chunk in param_chunks:
            stepped_lists.append(_make_stepped_list(param_chunk, num=num))
    else:
        raise ValueError(
            "params must contain 3 values for the first movable and 2 values for each "
            "successive movable."
        )
    return stepped_lists


def _make_independently_stepped_lists(
    movers_len: int,
    params: list[Any] | Sequence[Any],
):
    num_params = 3  # It will always be start stop step for each axis
    stepped_lists = []
    params_len = len(params)
    if params_len % movers_len == 0 and params_len % num_params == 0:
        it = iter(params)
        param_chunks = iter(lambda: tuple(itertools.islice(it, num_params)), ())
        for param_chunk in param_chunks:
            stepped_lists.append(_make_stepped_list(param_chunk))
    else:
        raise ValueError(f"params must contain {num_params} values for each movable")
    return stepped_lists


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[Any],
        Field(
            description="Start, stop, and step values for the first movable, and start "
            "and step values for each successive movable, 'start1, stop1, step1, "
            "start2, step 2, ..., startN, stepN' for every movable in `movers`."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over one multi-motor trajectory with specified step size.
    Generates lists of points for each trajectory for bp.list_scan.
    """
    movers_len = len(movers)
    stepped_lists = _make_concurrently_stepped_lists(
        movers_len=movers_len, params=params
    )
    metadata = metadata or {}
    args = _make_args(movers=movers, params=stepped_lists, num_params=1)
    yield from bp.list_scan(tuple(detectors), *args, md=metadata)


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
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[Any],
        Field(
            description="Start, stop, and step values for the first movable, and start "
            "and step values for each successive movable, 'start1, stop1, step1, "
            "start2, step 2, ..., startN, stepN' for every movable in `movers`."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over multi-motor trajectory relative to position with specified step size.
    Generates lists of points for each trajectory for bp.rel_list_scan.
    """
    movers_len = len(movers)
    stepped_lists = _make_concurrently_stepped_lists(
        movers_len=movers_len, params=params
    )
    metadata = metadata or {}
    args = _make_args(movers=movers, params=stepped_lists, num_params=1)
    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[Any],
        Field(
            description="Start, stop, and step values 'start1, stop1, step1, ..., "
            "startN, stepN' for every movable in `movers`."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over independent multi-motor trajectories with specified step size.
    Generates lists of points for each trajectory for bp.list_grid_scan.
    """
    movers_len = len(movers)
    stepped_lists = _make_independently_stepped_lists(
        movers_len=movers_len, params=params
    )
    metadata = metadata or {}
    args = _make_args(movers=movers, params=stepped_lists, num_params=1)
    yield from bp.list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    movers: Annotated[
        Sequence[Movable | Motor],
        Field(description="One or more movable to move during the scan."),
    ],
    params: Annotated[
        list[Any],
        Field(
            description="Start, stop, and step values 'start1, stop1, step1, ..., "
            "startN, stepN' for every movable in `movers`."
        ),
    ],
    snake_axes: bool = False,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan over independent multi-motor relative trajectories with specified step size.
    Generates lists of points for each trajectory for bp.rel_list_grid_scan.
    """
    movers_len = len(movers)
    stepped_lists = _make_independently_stepped_lists(
        movers_len=movers_len, params=params
    )
    metadata = metadata or {}
    args = _make_args(movers=movers, params=stepped_lists, num_params=1)
    yield from bp.rel_list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
