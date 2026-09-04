from collections.abc import Sequence
from typing import Annotated as A

from bluesky.protocols import Readable
from ophyd_async.core import AsyncReadable
from pydantic import BeforeValidator, Field

from dodal.plans.scans.types import (
    MovableListOfPoints,
    MovableStartStep,
    MovableStartStop,
    MovableStartStopNum,
    MovableStartStopStep,
)
from dodal.plans.scans.validators import trajectory_validator

DetectorsA = A[
    Sequence[Readable | AsyncReadable],
    Field(
        description="Set of readable devices, will take a reading at each point",
    ),
]

MovableStartStepA = A[
    MovableStartStep,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, step)."
    ),
    BeforeValidator(
        trajectory_validator(
            length=3,
            template="(movable, start, step)",
            expected_type=MovableStartStop,
        )
    ),
]

MovableStartStopA = A[
    MovableStartStop,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, stop)."
    ),
    BeforeValidator(
        trajectory_validator(
            length=3,
            template="(movable, start, stop)",
            expected_type=MovableStartStop,
        )
    ),
]

MovableStartStopNumA = A[
    MovableStartStopNum,
    Field(
        description="Additional trajectories, each specified as a tuple of "
        "(movable, start, stop, num)."
    ),
    BeforeValidator(
        trajectory_validator(
            length=4,
            template="(movable, start, stop, num)",
            expected_type=MovableStartStopNum,
        )
    ),
]

MovableListOfPointsA = A[
    MovableListOfPoints,
    Field(
        description="List of tuples (device, positions). For concurrent \
            trajectories, provide '[(movable1, [point1, point2, ...]), (movable2, \
            [point1, point2, ...]), ... , (movableN, [point1, point2, ...])]'. Number \
            of points for each movable must be equal."
    ),
    BeforeValidator(
        trajectory_validator(
            length=2,
            template="(movable, [point1, point2, ...])",
            expected_type=MovableListOfPoints,
        )
    ),
]

MovableStartStopStepA = A[
    MovableStartStopStep,
    Field(
        description="Tuple containing (movable, start, stop, step) for a scan trajectory."
    ),
    BeforeValidator(
        trajectory_validator(
            length=4,
            template="(movable, start, stop, step)",
            expected_type=MovableStartStopStep,
        )
    ),
]
