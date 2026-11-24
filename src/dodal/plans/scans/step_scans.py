from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Any

import bluesky.plans as bp
import numpy as np
from bluesky.protocols import Movable, Readable
from pydantic import Field, validate_call

from dodal.common import MsgGenerator


def _round_list_elements(stepped_list, params) -> list[float]:
    decimals = [Decimal(str(param)) for param in params]
    exponents = [d.as_tuple().exponent for d in decimals]
    decimal_places = [-exponent for exponent in exponents]  # type: ignore
    max_decimal_places = max(decimal_places)
    return np.round(stepped_list, decimals=max_decimal_places).tolist()


def _make_stepped_list_step(start: float, stop: float, step: float) -> list:
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


def _make_stepped_list_num(start, step, num) -> list:
    stepped_list = [start + (n * step) for n in range(num)]
    rounded_stepped_list = _round_list_elements(
        stepped_list=stepped_list, params=[start, step]
    )
    return rounded_stepped_list


def _make_step_scan_args(
    params: list[tuple[Movable, list[float | int]]], grid: bool
) -> tuple[list[Any], list[float]]:
    args = []
    shape = []
    stepped_list_length = None

    first_movable_param, *additional_movable_params = params
    if len(first_movable_param[1]) == 3:
        start, stop, step = first_movable_param[1]
        stepped_list = _make_stepped_list_step(start, stop, step)
        stepped_list_length = len(stepped_list)
        args.append(first_movable_param[0])
        args.append(stepped_list)
        shape.append(stepped_list_length)
    else:
        raise ValueError(
            f"You provided {len(first_movable_param[1])} parameters for {first_movable_param[0]}, rather than 3."
        )
    for param in additional_movable_params:
        if grid:
            if len(param[1]) == 3:
                start, stop, step = param[1]
                stepped_list = _make_stepped_list_step(start, stop, step)
                args.append(param[0])
                args.append(stepped_list)
                shape.append(len(stepped_list))
            else:
                raise ValueError(
                    f"You provided {len(param[1])} parameters for {param[0]}, rather than 3."
                )
        else:
            if len(param[1]) == 2:
                start, step = param[1]
                stepped_list = _make_stepped_list_num(start, step, stepped_list_length)
                args.append(param[0])
                args.append(stepped_list)
            else:
                raise ValueError(
                    f"You provided {len(param[1])} parameters {param[0]}, rather than 2."
                )

    return args, shape


@validate_call(config={"arbitrary_types_allowed": True})
def step_scan(
    detectors: Annotated[
        Sequence[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        list[tuple[Movable, list[float | int]]],
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
    args, shape = _make_step_scan_args(params, grid=False)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_scan(tuple(detectors), *args, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_scan(
    detectors: Annotated[
        Sequence[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        list[tuple[Movable, list[float | int]]],
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
    args, shape = _make_step_scan_args(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )


@validate_call(config={"arbitrary_types_allowed": True})
def step_rscan(
    detectors: Annotated[
        Sequence[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        list[tuple[Movable, list[float | int]]],
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
    args, shape = _make_step_scan_args(params, grid=False)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_scan(tuple(detectors), *args, md=metadata)


@validate_call(config={"arbitrary_types_allowed": True})
def step_grid_rscan(
    detectors: Annotated[
        Sequence[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
        ),
    ],
    params: Annotated[
        list[tuple[Movable, list[float | int]]],
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
    args, shape = _make_step_scan_args(params, grid=True)
    metadata = metadata or {}
    metadata["shape"] = shape

    yield from bp.rel_list_grid_scan(
        tuple(detectors), *args, snake_axes=snake_axes, md=metadata
    )
