from dataclasses import dataclass

from ophyd_async.core import SignalRW, derived_signal_rw
from ophyd_async.epics.motor import Motor, MotorMoveLogic

from dodal.log import LOGGER


class MotorStringSetpoint(Motor):
    """Create a float interface for an string-valued setpoint PV Motor.

    Undulator motors expose their setpoint PV as a string rather than a numeric
    value. This helper creates both the underlying string signal and a derived
    float signal that transparently converts between ``float`` values used by
    clients and the string representation required by the IOC.
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
