from collections.abc import Sequence
from typing import Annotated as A
from typing import Any, TypeVar

from bluesky.protocols import Movable, Readable
from ophyd_async.core import AsyncReadable
from pydantic import BeforeValidator, Field

from dodal.plans.scans.validators import trajectory_validator, validate_start_stop_step

Number = float | int
T = TypeVar("T")

DetectorsA = A[
    Sequence[Readable | AsyncReadable],
    Field(
        description="Set of readable devices, will take a reading at each point",
    ),
]

MovableStartStep = tuple[Movable[Number], Number, Number]

MovableStartStepA = A[
    MovableStartStep,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, step)."
    ),
]

MovableStartStop = tuple[Movable[Number], Number, Number]

MovableStartStopA = A[
    MovableStartStop,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, stop)."
    ),
]

MovableStartStopNum = tuple[Movable[Number], Number, Number, int]

MovableStartStopNumA = A[
    MovableStartStopNum,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, stop, num)."
    ),
]

MovableListOfPoints = tuple[Movable[Any], list[Any]]

MovableListOfPointsA = A[
    MovableListOfPoints,
    Field(
        description="List of tuples (device, positions). For concurrent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'. Number \
            of points for each movable must be equal."
    ),
]

MovableStartStopStep = tuple[Movable[Number], Number, Number, Number]


MovableStartStopStepA = A[
    MovableStartStopStep,
    Field(
        description="Tuple containing (movable, start, stop, step) for a scan trajectory."
    ),
    BeforeValidator(
        trajectory_validator(
            length=4,
            template="(movable, start, stop, step)",
            validate=validate_start_stop_step,
        )
    ),
]
