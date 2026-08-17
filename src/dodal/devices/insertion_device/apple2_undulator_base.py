import abc
import asyncio
from typing import Generic, TypeVar

from bluesky.protocols import Checkable
from ophyd_async.core import DEFAULT_TIMEOUT, SignalR, SignalW, wait_for_value

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.enum import UndulatorGateStatus

T = TypeVar("T")


def estimate_motor_timeout(setpoint: float, readback: float, velocity: float):
    return abs((setpoint - readback) * 2.0 / velocity) + DEFAULT_TIMEOUT


async def estimate_motor_timeout_from_signals(
    setpoint: SignalR[float], readback: SignalR[float], velocity: SignalR[float]
) -> float:
    setpoint_val, readback_val, velocity_val = await asyncio.gather(
        setpoint.get_value(), readback.get_value(), velocity.get_value()
    )
    return estimate_motor_timeout(setpoint_val, readback_val, velocity_val)


async def undulator_check_move(
    status: SignalR[EnabledDisabledUpper], gate: SignalR[UndulatorGateStatus]
) -> None:
    """Verify that an undulator is able to accept a move request.

    Raises:
        RuntimeError: If the undulator is disabled or already moving.
    """
    status_val, gate_val = await asyncio.gather(status.get_value(), gate.get_value())
    if status_val is EnabledDisabledUpper.DISABLED:
        raise RuntimeError(f"{status.name} is DISABLED and cannot move.")
    if gate_val is UndulatorGateStatus.OPEN:
        raise RuntimeError(f"{gate.name} is already in motion.")


async def set_move_and_wait_for_gate(
    gate: SignalR[UndulatorGateStatus], set_move: SignalW[int], timeout: float | None
):
    await set_move.set(value=1, timeout=timeout)
    await wait_for_value(gate, UndulatorGateStatus.CLOSE, timeout=timeout)


class UndulatorBase(abc.ABC, Checkable[T], Generic[T]):
    """Base class for Apple2 undulator devices that use gated motion.

    Subclasses implement writing demand positions and estimating move
    timeouts, while this class provides the common sequence of:


    * writing demand positions,
    * triggering the controller move,

    Attributes:
        set_move: Signal used to trigger motion after demands have been written.
    """

    # Nothing move until this is set to 1 and it will return to 0 when done
    set_move: SignalW[int]

    @abc.abstractmethod
    async def set_demand_positions(self, value: T) -> None:
        """Set the demand positions on the device without actually hitting move."""

    @abc.abstractmethod
    async def check_value(self, value: T) -> None:
        """Check the new position is valid."""

    @abc.abstractmethod
    async def get_timeout(self) -> float | None:
        """Get the timeout for the move based on an estimate of how long it will take."""
