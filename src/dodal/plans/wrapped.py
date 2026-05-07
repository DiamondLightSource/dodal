from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Any, TypeVar

import bluesky.plans as bp
import numpy as np
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
    - Forcing uniqueness or orderedness of Readables.
    - Limits and metadata (e.g. units).
"""

T = TypeVar("T")


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


@validate_call(config={"arbitrary_types_allowed": True})
def num_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For concurrent "
            "trajectories, provide '[movable1, start1, stop1, movable2, start2, stop2, "
            "... , movableN, startN, stopN]'."
        ),
    ],
    num: int,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by number of points along scan trajector(y/ies). Wraps
    bluesky.plans.scan(det, *args, num, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)

    yield from bp.scan(tuple(detectors), *params, num=num, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For independent \
            trajectories, provide '[(movable1, [start1, stop1, num1]), (movable2, \
            [start2, stop2, num2]), ... , (movableN, [startN, stopN, numN])]'."
        ),
    ],
    snake_axes: list | bool = True,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent multi-motor trajectories.

    The scan is defined by number of points along scan trajectories. Snakes all fast
    axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata).
    """
    yield from bp.grid_scan(
        tuple(detectors), *params, snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def num_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For concurrent \
            trajectories, provide '[movable1, start1, stop1, movable2, start2, stop2, \
            ... , movableN, startN, stopN]'."
        ),
    ],
    num: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position(s).

    The scan is defined by number of points along scan trajector(y/ies). Wraps
    bluesky.plans.rel_scan(det, *args, num, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = (num,)

    yield from bp.rel_scan(tuple(detectors), *params, num=num, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For independent \
            trajectories, provide '[(movable1, [start1, stop1, num1]), (movable2, \
            [start2, stop2, num2]), ... , (movableN, [startN, stopN, numN])]'."
        ),
    ],
    snake_axes: list | bool = True,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories, relative to current positions.

    The scan is defined by number of points along scan trajectories. Snakes all fast
    axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.rel_grid_scan(det, *args, snake_axes, md=metadata).
    """
    yield from bp.rel_grid_scan(
        tuple(detectors), *params, snake_axes=snake_axes, md=metadata
    )


def _make_list_scan_shape(
    params: Sequence[Movable | list[float | int]],
) -> tuple[int, ...]:
    for param in params:
        # List arg must all be same size. If list missing or not same size, this will
        # be validated by bp.list_scan.
        if isinstance(param, list):
            return (len(param),)
    return ()


@validate_call(config={"arbitrary_types_allowed": True})
def list_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        list[Movable | list[float | int]],
        Field(
            description="List of tuples (device, positions). For concurrent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'. Number \
            of points for each movable must be equal."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.list_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(params)

    # Not sure about this one
    yield from bp.list_scan(tuple(detectors), *tuple(params), md=metadata)  # type: ignore


@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | list[float | int]],
        Field(
            description="List of tuples (device, positions). For independent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories.

    The scan is defined by providing a list of points for each scan trajectory. Snakes
    all fast axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.list_grid_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    shape = []
    for param in params:
        if isinstance(param, list):
            shape.append(len(param))
    metadata["shape"] = tuple(shape)

    yield from bp.list_grid_scan(
        tuple(detectors), *params, snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def list_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | list[float | int]],
        Field(
            description="List of tuples (device, positions). For concurrent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'. Number \
            of points for each movable must be equal."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position.

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(params)
    yield from bp.rel_list_scan(tuple(detectors), *params, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def list_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | list[float | int]],
        Field(
            description="List of tuples (device, positions). For independent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories, relative to current positions.

    The scan is defined by providing a list of points for each scan trajectory. Snakes
    all fast axes by default (all axes but the first axis provided). Wraps
    bluesky.plans.rel_list_grid_scan(det, *args, md=metadata).
    """
    metadata = metadata or {}
    metadata["shape"] = _make_list_scan_shape(params)
    yield from bp.rel_list_grid_scan(
        tuple(detectors), *params, snake_axes=snake_axes, md=metadata
    )


def _round_list_elements(
    stepped_list: list[float | int], params: list[float | int]
) -> list[float | int]:
    decimals = [Decimal(str(param)) for param in params]
    exponents = [d.as_tuple().exponent for d in decimals]
    decimal_places = [-exponent for exponent in exponents]  # type: ignore
    max_decimal_places = max(decimal_places)
    return np.round(stepped_list, decimals=max_decimal_places).tolist()


def _make_stepped_list_step(
    start: float, stop: float, step: float
) -> list[float | int]:
    if start == stop:
        raise ValueError(
            f"Start ({start}) and stop ({stop}) values cannot be the same."
        )
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


def _make_stepped_list_num(start: float, step: float, num: int) -> list[float | int]:
    if num <= 0:
        raise ValueError()
    stepped_list = [start + (n * step) for n in range(num)]
    rounded_stepped_list = _round_list_elements(
        stepped_list=stepped_list, params=[start, step]
    )
    return rounded_stepped_list


def _make_step_scan_args_and_shape(
    params: Sequence[Movable | float | int],
    grid: bool,
) -> tuple[list[Movable | list[float]], tuple[int, ...]]:

    def require(
        value: object,
        expected: type[T] | tuple[type, ...],
        name: str,
    ) -> T:
        expected_tuple = expected if isinstance(expected, tuple) else (expected,)
        if not isinstance(value, expected_tuple):
            allowed = ", ".join(t.__name__ for t in expected_tuple)
            raise ValueError(
                f"Parameter {name} must be one of type ({allowed}), got {type(value).__name__}"
            )
        return value  # type: ignore[return-value]

    def parse_full_axis(
        values: Sequence[Movable | float | int],
    ) -> tuple[Movable, float, float, float]:
        if len(values) != 4:
            raise ValueError(
                f"Full axis must be movable, start, stop, step. You provided {values}"
            )
        movable = require(values[0], Movable, "movable")
        start = require(values[1], (int, float), "start")
        stop = require(values[2], (int, float), "stop")
        step = require(values[3], (int, float), "step")

        return movable, start, stop, step

    def parse_relative_axis(
        values: Sequence[Movable | float | int],
    ) -> tuple[Movable, float, float]:
        if len(values) != 3:
            raise ValueError(
                f"Relative axis must be movable, start, step. You provided {values}"
            )
        movable = require(values[0], Movable, "movable")
        start = require(values[1], (int, float), "start")
        step = require(values[2], (int, float), "step")

        return movable, start, step

    if len(params) < 4:
        raise ValueError("At least one axis must provide (movable, start, stop, step)")

    args: list[Movable | list[float]] = []
    shape: list[int] = []

    # First axis defines scan length
    movable, start, stop, step = parse_full_axis(params[:4])

    values = _make_stepped_list_step(start, stop, step)
    stepped_list_length = len(values)

    args.extend([movable, values])
    shape.append(stepped_list_length)

    remaining = params[4:]

    chunk_size = 4 if grid else 3

    if len(remaining) % chunk_size != 0:
        raise ValueError("Incorrect number of parameters for additional axes")

    for i in range(0, len(remaining), chunk_size):
        chunk = remaining[i : i + chunk_size]
        if grid:
            movable, start, stop, step = parse_full_axis(chunk)
            values = _make_stepped_list_step(start, stop, step)
            shape.append(len(values))
        else:
            movable, start, step = parse_relative_axis(chunk)
            values = _make_stepped_list_num(start, step, stepped_list_length)
        args.extend([movable, values])

    return args, tuple(shape)


@validate_call(config={"arbitrary_types_allowed": True})
def step_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For concurrent \
            trajectories, provide '[(movable1, [start1, stop1, step1]), (movable2, \
            [start2, step2]), ... , (movableN, [startN, stepN])]'."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args_and_shape(params, grid=False)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_scan(tuple(detectors), *tuple(args), md=metadata)  # type: ignore


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For independent \
            trajectories, provide '[(movable1, [start1, stop1, step1]), (movable2, \
            [start2, stop2, step2]), ... , (movableN, [startN, stopN, stepN])]'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata). Snakes all fast axes by
    default (all axes but the first axis provided).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args_and_shape(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def step_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For concurrent \
            trajectories, provide '[(movable1, [start1, stop1, step1]), (movable2, \
            [start2, step2]), ... , (movableN, [startN, stepN])]'."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args_and_shape(params, grid=False)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        Sequence[Movable | float | int],
        Field(
            description="List of tuples (device, parameter). For independent \
            trajectories, provide '[(movable1, [start1, stop1, step1]), (movable2, \
            [start2, stop2, step2]), ... , (movableN, [startN, stopN, stepN])]'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata). Snakes all fast axes by
    default (all axes but the first axis provided).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args_and_shape(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

    print(args)

    yield from bp.rel_list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
