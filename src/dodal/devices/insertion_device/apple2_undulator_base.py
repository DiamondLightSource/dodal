import abc
import asyncio
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    SignalR,
    SignalW,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER

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


class SafeUndulatorMoverBase(abc.ABC, StandardReadable, Movable[T], Generic[T]):
    # Nothing move until this is set to 1 and it will return to 0 when done
    set_move: SignalW[int]

    def __init__(self, prefix: str, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def move(self, value: T):
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.raise_if_cannot_move()
        await self.set_demand_positions(value)
        timeout = await self.get_timeout()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await set_move_and_wait_for_gate(self.gate, self.set_move, timeout)

    @abc.abstractmethod
    async def set_demand_positions(self, value: T) -> None:
        """Set the demand positions on the device without actually hitting move."""

    @abc.abstractmethod
    async def get_timeout(self) -> float | None:
        """Get the timeout for the move based on an estimate of how long it will take."""

    async def raise_if_cannot_move(self) -> None:
        await undulator_check_move(self.status, self.gate)
