from collections.abc import Sequence
from typing import Any, TypeVar

from bluesky.protocols import Movable, Readable
from pydantic import PositiveInt

T = TypeVar("T")

Detectors = Sequence[Readable]

MovableStartStep = tuple[Movable[float], float, float]

MovableStartStepNum = tuple[Movable[float], float, float, PositiveInt]

MovableStartStop = tuple[Movable[float], float, float]

MovableStartStopNum = tuple[Movable[float], float, float, PositiveInt]

MovableListOfPositions = tuple[Movable[Any], Sequence[Any]]

MovableStartStopStep = tuple[Movable[float], float, float, float]
