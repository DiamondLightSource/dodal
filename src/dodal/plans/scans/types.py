from collections.abc import Sequence
from typing import Any

from bluesky.protocols import Movable, Readable
from ophyd_async.core import AsyncReadable
from pydantic import PositiveInt

Detectors = Sequence[Readable | AsyncReadable]

MovableStartStep = tuple[Movable[float], float, float]

MovableStartStepNum = tuple[Movable[float], float, float, PositiveInt]

MovableStartStop = tuple[Movable[float], float, float]

MovableStartStopNum = tuple[Movable[float], float, float, PositiveInt]

MovableListOfPositions = tuple[Movable[Any], Sequence[Any]]

MovableStartStopStep = tuple[Movable[float], float, float, float]
