import asyncio
from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Any

from ophyd_async.core import (
    SignalW,
    StandardReadable,
    StrictEnum,
    set_and_wait_for_value,
)
from ophyd_async.epics.motor import Motor


class DeferMoves(StrictEnum):
    ON = "Defer On"
    OFF = "Defer Off"


@asynccontextmanager
async def _deferred_move(signal: SignalW[DeferMoves]):
    await signal.set(DeferMoves.ON)
    try:
        yield
    finally:
        await signal.set(DeferMoves.OFF)


def combined_move_to_motor_setpoints(
    combined_move: Mapping[str, Any], device: StandardReadable
) -> dict[Motor, float]:
    motor_moves = {}
    for motor_name, new_setpoint in combined_move.items():
        if new_setpoint is not None and isinstance(new_setpoint, float | int):
            try:
                motor = getattr(device, motor_name)
                assert isinstance(motor, Motor)
            except Exception as e:
                raise LookupError(
                    f"Motor {motor_name} not found in combined move"
                ) from e
            motor_moves[motor] = new_setpoint
    return motor_moves


async def do_deferred_move(
    defer_signal: SignalW[DeferMoves],
    moves: dict[Motor, float],
    timeout: float,
):
    """This will move all motion together in a deferred move.

    Once defer_move is on, sets to any axis do not immediately move the axis. Instead
    the setpoint will go to that value. Then, when defer_move is switched off all
    axes will move at the same time. The put callbacks on the axes themselves will
    only come back after the motion on that axis finished.
    """
    finished = []

    async with _deferred_move(defer_signal):
        for axis, value in moves.items():
            # A regular motor move would do this internally but we need to set the
            # user_setpoint (see below)
            await axis.check_value(value)

            # Wait for the setpoint to reach the value so we know the IOC has received
            # the put
            status = await set_and_wait_for_value(
                axis.user_setpoint,
                value,
                timeout=timeout,
                wait_for_set_completion=False,
            )

            finished.append(status)

    await asyncio.gather(*finished)
