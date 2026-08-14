import asyncio
from abc import ABC
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    SignalR,
    SignalRW,
    SignalW,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor, MotorMoveLogic

from dodal.log import LOGGER


def estimate_motor_timeout(setpoint: float, readback: float, velocity: float):
    return abs((setpoint - readback) * 2.0 / velocity) + DEFAULT_TIMEOUT


async def estimate_motor_timeout_from_signals(
    setpoint: SignalR[float], readback: SignalR[float], velocity: SignalR[float]
) -> float:
    setpoint_val, readback_val, velocity_val = await asyncio.gather(
        setpoint.get_value(), readback.get_value(), velocity.get_value()
    )
    return estimate_motor_timeout(setpoint_val, readback_val, velocity_val)


T = TypeVar("T", contravariant=True)


class UndulatorCoordinatableMove(Protocol, Generic[T]):
    """Interface for an undulator component that supports coordinated movement.

    Components implementing this protocol expose the operations required by a
    parent device to coordinate multiple axes as a single move. Demand positions
    can be written independently of triggering motion, allowing all component
    demands to be set before any movement is started.

    The parent device is responsible for coordinating the movement by:

    1. Setting demand positions on all components.
    2. Calculating a timeout for each component.
    3. Triggering all components to move together.
    4. Waiting for the shared undulator gate to indicate that movement is complete.

    Attributes:
        set_move: Signal used to trigger movement after the demand position has
            been set. Writing ``1`` starts the move; the signal is reset by the IOC.
    """

    set_move: SignalW[int]

    async def set_demand_positions(self, value: T): ...

    async def get_timeout(self) -> float: ...


class MotorStringSetpoint(Motor, ABC):
    """Create a float interface for an string-valued setpoint PV Motor.

    Undulator motors expose their setpoint PV as a string rather than a numeric
    value. This helper creates both the underlying string signal and a derived
    float signal that transparently converts between ``float`` values used by
    clients and the string representation required by the IOC. Sub classes must provide
    the user_setpoint_str signal.
    """

    user_setpoint_str: SignalRW[str]

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, name)
        self.user_setpoint = derived_signal_rw(
            self._read_user_setpoint,
            self._set_user_setpoint,
            setpoint=self.user_setpoint_str,
        )

    async def _set_user_setpoint(self, value: float) -> None:
        await self.user_setpoint_str.set(str(value))

    def _read_user_setpoint(self, setpoint: str) -> float:
        return float(setpoint)


@dataclass
class UnstoppableMotorMoveLogic(MotorMoveLogic):
    """Motor move logic for motors that cannot be stopped."""

    async def stop(self):
        LOGGER.warning(f"Stopping {self.readback.name} is not supported.")
