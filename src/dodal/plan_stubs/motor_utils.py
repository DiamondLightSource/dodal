import uuid
from collections.abc import Generator
from typing import Any

from bluesky import plan_stubs as bps
from bluesky.preprocessors import finalize_wrapper, pchain
from bluesky.utils import Msg, MsgGenerator, make_decorator
from ophyd_async.core import Device
from ophyd_async.epics.motor import Motor


class MoveTooLarge(Exception):
    def __init__(
        self,
        axis: Motor,
        maximum_move: float,
        position: float,
        *args: object,
    ) -> None:
        self.axis = axis
        self.maximum_move = maximum_move
        self.position = position
        super().__init__(*args)


def check_and_cache_values(
    devices_and_positions: dict[Motor, float],
    smallest_move: float,
    maximum_move: float,
) -> Generator[Msg, Any, dict[Motor, float]]:
    """Caches the positions of all Motors on specified device if they are within
    smallest_move of home_position. Throws MoveTooLarge if they are outside maximum_move
    of the home_position
    """
    positions = {}
    for axis, new_position in devices_and_positions.items():
        position = yield from bps.rd(axis)
        if abs(position - new_position) > maximum_move:
            raise MoveTooLarge(axis, maximum_move, position)
        if abs(position - new_position) > smallest_move:
            positions[axis] = position
    return positions


def home_and_reset_wrapper(
    plan: MsgGenerator,
    device: Device,
    smallest_move: float,
    maximum_move: float,
    group: str | None = None,
    wait_for_all: bool = True,
) -> MsgGenerator:
    home_positions = {
        axis: 0.0 for _, axis in device.children() if isinstance(axis, Motor)
    }
    return move_and_reset_wrapper(
        plan, home_positions, smallest_move, maximum_move, group, wait_for_all
    )


def move_and_reset_wrapper(
    plan: MsgGenerator,
    device_and_positions: dict[Motor, float],
    smallest_move: float,
    maximum_move: float,
    group: str | None = None,
    wait_for_all: bool = True,
) -> MsgGenerator:
    """Wrapper that does the following:
       1. Caches the positions of all Motors on device
       2. Throws a MoveTooLarge exception if any positions are maximum_move away from home_position
       2. Moves any motor that is more than smallest_move away from the home_position to home_position
       3. Runs the specified plan
       4. Moves all motors back to their cached positions

    Args:
        plan (Callable[[], MsgGenerator]): The plan to move between homing and returning to the cache
        device (Device): The device to move. All Motors in the device will be cached and moved
        smallest_move (float): The smallest move that we care about doing the home and cache for.
                               Useful for not wearing out motors if you have large tolerances
        maximum_move (float): If any Motor starts this far from the home an exception is raised
                              and no moves occur
        home_position (float): The position to move every motor to after caching
        group (str, optional): If set the home move will be done using the home-{group}
                               group and the reset to cache done using reset-{group}
        wait_for_all (bool, optional): If true the home and reset to cache will be waited
                                       on. If false it is left up to the caller to wait on
                                       them. Defaults to True.
    """
    initial_positions = yield from check_and_cache_values(
        device_and_positions, smallest_move, maximum_move
    )

    def move_to_home():
        home_group = f"home-{group if group else str(uuid.uuid4())[:6]}"
        for axis, position in device_and_positions.items():
            if axis in initial_positions.keys():
                yield from bps.abs_set(axis, position, group=home_group)
        if wait_for_all:
            yield from bps.wait(home_group)

    def return_to_initial_position():
        reset_group = f"reset-{group if group else str(uuid.uuid4())[:6]}"
        for axis, position in initial_positions.items():
            yield from bps.abs_set(axis, position, group=reset_group)
        if wait_for_all:
            yield from bps.wait(reset_group)

    return (
        yield from finalize_wrapper(
            pchain(move_to_home(), plan),
            return_to_initial_position(),
        )
    )


home_and_reset_decorator = make_decorator(home_and_reset_wrapper)
