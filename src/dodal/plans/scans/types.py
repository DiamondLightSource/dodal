from collections.abc import Sequence
from typing import Any

from bluesky.protocols import Movable, Readable
from ophyd_async.core import AsyncReadable

Number = float | int

Detectors = Sequence[Readable | AsyncReadable]

MovableStartStep = tuple[Movable[Number], Number, Number]

MovableStartStop = tuple[Movable[Number], Number, Number]

MovableStartStopNum = tuple[Movable[Number], Number, Number, int]

MovableListOfPoints = tuple[Movable[Any], list[Any]]

MovableStartStopStep = tuple[Movable[Number], Number, Number, Number]
