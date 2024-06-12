from typing import Any, Generator

from bluesky import plan_stubs as bps
from bluesky.utils import Msg
from ophyd_async.epics.motion import Motor

from dodal.devices.motors import XYZPositioner


class OptionalXYZPosition:
    x_mm: float | None = None
    y_mm: float | None = None
    z_mm: float | None = None


class MoveTooLarge(Exception):
    def __init__(self, axis: Motor, maximum_move: float, *args: object) -> None:
        self.axis = axis
        self.maximum_move = maximum_move
        super().__init__(*args)


def cache_values_and_move(
    positioner: XYZPositioner,
    smallest_move: float,
    maximum_move: float,
    home_position: float = 0,
    group="lower_gonio",
    wait: bool = True,
) -> Generator[Msg, Any, OptionalXYZPosition]:
    positions = []
    for axis in [positioner.x, positioner.y, positioner.z]:
        position = yield from bps.rd(axis)
        if abs(position) > maximum_move:
            raise MoveTooLarge(axis, maximum_move)
        if abs(position - home_position) < smallest_move:
            position = None
        positions.append(position)
    yield from bps.abs_set(positioner.x, home_position, group=group)
    yield from bps.abs_set(positioner.y, home_position, group=group)
    yield from bps.abs_set(positioner.z, home_position, group=group)

    if wait:
        yield from bps.wait()
    return OptionalXYZPosition(*positions)
