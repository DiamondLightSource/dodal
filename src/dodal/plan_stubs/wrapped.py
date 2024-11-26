import itertools
from collections.abc import Mapping
from typing import Annotated, Any

import bluesky.plan_stubs as bps
from bluesky.protocols import Movable
from bluesky.utils import MsgGenerator

"""
Wrappers for Bluesky built-in plan stubs with type hinting
"""

Group = Annotated[str, "String identifier used by 'wait' or stubs that await"]


# After bluesky 1.14, bounds for stubs that move can be narrowed
# https://github.com/bluesky/bluesky/issues/1821
def set_absolute(
    movable: Movable, value: Any, group: Group | None = None, wait: bool = False
) -> MsgGenerator:
    """
    Set a device, wrapper for `bp.abs_set`.

    Args:
        movable (Movable): The device to set
        value (T): The new value
        group (Group | None, optional): The message group to associate with the
                                           setting, for sequencing. Defaults to None.
        wait (bool, optional): The group should wait until all setting is complete
                               (e.g. a motor has finished moving). Defaults to False.

    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """
    return (yield from bps.abs_set(movable, value, group=group, wait=wait))


def set_relative(
    movable: Movable, value: Any, group: Group | None = None, wait: bool = False
) -> MsgGenerator:
    """
    Change a device, wrapper for `bp.rel_set`.

    Args:
        movable (Movable): The device to set
        value (T): The new value
        group (Group | None, optional): The message group to associate with the
                                           setting, for sequencing. Defaults to None.
        wait (bool, optional): The group should wait until all setting is complete
                               (e.g. a motor has finished moving). Defaults to False.

    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """

    return (yield from bps.rel_set(movable, value, group=group, wait=wait))


def move(moves: Mapping[Movable, Any], group: Group | None = None) -> MsgGenerator:
    """
    Move a device, wrapper for `bp.mv`.

    Args:
        moves (Mapping[Movable, T]): Mapping of Movables to target positions
        group (Group | None, optional): The message group to associate with the
                                           setting, for sequencing. Defaults to None.

    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """

    return (
        # type ignore until https://github.com/bluesky/bluesky/issues/1809
        yield from bps.mv(*itertools.chain.from_iterable(moves.items()), group=group)  # type: ignore
    )


def move_relative(
    moves: Mapping[Movable, Any], group: Group | None = None
) -> MsgGenerator:
    """
    Move a device relative to its current position, wrapper for `bp.mvr`.

    Args:
        moves (Mapping[Movable, T]): Mapping of Movables to target deltas
        group (Group | None, optional): The message group to associate with the
                                           setting, for sequencing. Defaults to None.

    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """

    return (
        # type ignore until https://github.com/bluesky/bluesky/issues/1809
        yield from bps.mvr(*itertools.chain.from_iterable(moves.items()), group=group)  # type: ignore
    )


def sleep(time: float) -> MsgGenerator:
    """
    Suspend all action for a given time, wrapper for `bp.sleep`

    Args:
        time (float): Time to wait in seconds

    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """

    return (yield from bps.sleep(time))


def wait(
    group: Group | None = None,
    timeout: float | None = None,
) -> MsgGenerator:
    """
    Wait for a group status to complete, wrapper for `bp.wait`.
    Does not expose move_on, as when used as a stub will not fail on Timeout.

    Args:
        group (Group | None, optional): The name of the group to wait for, defaults
                                           to None, in which case waits for all
                                           groups that have not yet been awaited.
        timeout (float | None, default=None): a timeout in seconds


    Returns:
        MsgGenerator: Plan

    Yields:
        Iterator[MsgGenerator]: Bluesky messages
    """

    return (yield from bps.wait(group, timeout=timeout))
