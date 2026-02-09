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


def _make_num_scan_args(
    params: list[tuple[Movable | Motor, list[float | int]]], num: int | None = None
):
    shape = []
    if num:
        shape = [num]
        for param in params:
            if len(param[1]) == 2:
                pass
            else:
                raise ValueError("You must provide 'start stop' for each motor.")
    else:
        for param in params:
            if len(param[1]) == 3:
                shape.append(param[1][-1])
            else:
                raise ValueError(
                    "You must provide 'start stop step' for each motor in a grid scan."
                )

    args = []
    for param in params:
        args.append(param[0])
        args.extend(param[1])
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
        list[tuple[Movable | Motor, list[float | int]]],
        Field(
            description="List of tuples (device, parameter). For concurrent \
            trajectories, provide '[(movable1, [start1, stop1]), (movable2, [start2, \
            stop2]), ... , (movableN, [startN, stopN])]'."
        ),
    ],
    num: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by number of points along scan trajector(y/ies).
    Wraps bluesky.plans.scan(det, *args, num, md=metadata).
    """
    # TODO: move to using Range spec and spec_scan when stable and tested at v1.0
    args, shape = _make_num_scan_args(params, num)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.scan(tuple(detectors), *args, num=num, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_scan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        list[tuple[Movable | Motor, list[float | int]]],
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

    The scan is defined by number of points along scan trajectories.
    Wraps bluesky.plans.grid_scan(det, *args, snake_axes, md=metadata).
    """
    # TODO: move to using Range spec and spec_scan when stable and tested at v1.0
    args, shape = _make_num_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.grid_scan(tuple(detectors), *args, snake_axes=snake_axes, md=metadata)


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
        list[tuple[Movable | Motor, list[float | int]]],
        Field(
            description="List of tuples (device, parameter). For concurrent \
            trajectories, provide '[(movable1, [start1, stop1]), (movable2, [start2, \
            stop2]), ... , (movableN, [startN, stopN])]'."
        ),
    ],
    num: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position(s).

    The scan is defined by number of points along scan trajector(y/ies).
    Wraps bluesky.plans.rel_scan(det, *args, num, md=metadata).
    """
    # TODO: move to using Range spec and spec_scan when stable and tested at v1.0
    args, shape = _make_num_scan_args(params, num)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_scan(tuple(detectors), *args, num=num, md=metadata)


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def num_grid_rscan(
    detectors: Annotated[
        Sequence[Readable | AsyncReadable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    params: Annotated[
        list[tuple[Movable | Motor, list[float | int]]],
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

    The scan is defined by number of points along scan trajectories.
    Wraps bluesky.plans.rel_grid_scan(det, *args, md=metadata).
    """
    # TODO: move to using Range spec and spec_scan when stable and tested at v1.0
    args, shape = _make_num_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


def _make_list_scan_args(
    params: dict[Movable | Motor, list[float | int]], grid: bool | None = None
):
    shape = []
    args = []
    for param in params:
        shape.append(len(params[param]))
        args.append(param)
        args.append(params[param])

    if not grid:
        shape = list(set(shape))
        if len(shape) > 1:
            raise ValueError("Lists of motor positions are not equal in length.")

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
            description="Dictionary of 'device: parameter' keys. For all trajectories, \
            provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, \
            ...]}'. Number of points for each movable must be equal."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent single or multi-motor trajector(y/ies).

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.list_scan(det, *args, md=metadata).
    """
    args, shape = _make_list_scan_args(params=params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_scan(tuple(detectors), *args, md=metadata)


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
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: parameter' keys. For all trajectories, \
            provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, \
            ...]}'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories.

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.list_grid_scan(det, *args, md=metadata).
    """
    args, shape = _make_list_scan_args(params=params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

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
            description="Dictionary of 'device: parameter' keys. For all trajectories, \
            provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, \
            ...]}'. Number of points for each movable must be equal."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajector(y/ies), relative to current position.

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    args, shape = _make_list_scan_args(params=params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


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
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: parameter' keys. For all trajectories, \
            provide '{movable1: [point1, point2, ... ], movableN: [point1, point2, \
            ...]}'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories, relative to current positions.

    The scan is defined by providing a list of points for each scan trajectory.
    Wraps bluesky.plans.rel_list_grid_scan(det, *args, md=metadata).
    """
    args, shape = _make_list_scan_args(params=params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

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


def _make_step_scan_args(
    params: dict[Movable | Motor, list[float | int]], grid: bool | None = None
):
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
            if grid:
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
            else:
                if len(params[param]) == 2:
                    stepped_list, stepped_list_length = _make_stepped_list(
                        params=params[param], num=stepped_list_length
                    )
                    args.append(param)
                    args.append(stepped_list)
                else:
                    raise ValueError(
                        f"You provided {len(params[param])} parameters, rather than 2."
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
            description="Dictionary of 'device: parameter' keys. For concurrent \
            trajectories, provide '{movable1: [start1, stop1, step1], movable2: \
            [start2, step2], ... , movableN: [startN, stepN]}'."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_scan(tuple(detectors), *args, md=metadata)


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
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: parameter' keys. For independent \
            trajectories, provide '{movable1: [start1, stop1, step1], ... , movableN: \
            [startN, stopN, stepN]}'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

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
            description="Dictionary of 'device: parameter' keys. For concurrent \
            trajectories, provide '{movable1: [start1, stop1, step1], movable2: \
            [start2, step2], ... , movableN: [startN, stepN]}'."
        ),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan concurrent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.rel_list_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args(params)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


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
    params: Annotated[
        dict[Movable | Motor, list[float | int]],
        Field(
            description="Dictionary of 'device: parameter' keys. For independent \
            trajectories, provide '{movable1: [start1, stop1, step1], ... , movableN: \
            [startN, stopN, stepN]}'."
        ),
    ],
    snake_axes: bool = True,  # Currently specifying axes to snake is not supported
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Scan independent trajectories with specified step size, relative to position.

    Generates list(s) of points for each trajectory, used with
    bluesky.plans.list_grid_scan(det, *args, md=metadata).
    """
    # TODO: move to using Linspace spec and spec_scan when stable and tested at v1.0
    args, shape = _make_step_scan_args(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
