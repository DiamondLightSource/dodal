from typing import Annotated as A

from pydantic import BeforeValidator, Field

from dodal.plans.scans.types import (
    Detectors,
    MovableListOfPoints,
    MovableStartStep,
    MovableStartStop,
    MovableStartStopNum,
    MovableStartStopStep,
)
from dodal.plans.scans.validators import trajectory_validator

DetectorsA = A[
    Detectors,
    Field(
        description="Set of readable devices, will take a reading at each point",
    ),
]

MovableStartStepA = A[
    MovableStartStep,
    Field(
        description="Trajectory defined by a movable, start position, and step size."
    ),
    BeforeValidator(
        trajectory_validator(
            length=3,
            template="(movable, start, step)",
            expected_type=MovableStartStep,
        )
    ),
]

MovableStartStopA = A[
    MovableStartStop,
    Field(
        description="Trajectory defined by a movable, start position, and stop position.",
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
        description="Trajectory defined by a movable, start position, stop position, "
        "and number of points."
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
        description="Trajectory defined by a movable and a list of positions to move to."
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
        description="Trajectory defined by a movable, start position, stop position, "
        "and step size."
    ),
    BeforeValidator(
        trajectory_validator(
            length=4,
            template="(movable, start, stop, step)",
            expected_type=MovableStartStopStep,
        )
    ),
]
