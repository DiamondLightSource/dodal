from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    MovableLogic,
    Reference,
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    derived_signal_r,
    wait_for_value,
)


@dataclass
class MovableWithToleranceLogic(MovableLogic[float]):
    within_tolerance: SignalR[bool]

    async def move(self, new_position: float, timeout: float | None) -> None:
        await self.setpoint.set(new_position, timeout=timeout)
        await wait_for_value(self.setpoint, new_position, timeout=timeout)
        # Once setpoint is at new position, we can check for tolerance signal to see if
        # true now as the within_tolerance window has updated to the new setpoint
        # position. Now it doesn't matter if motor steps are small or large.
        await wait_for_value(self.within_tolerance, True, timeout=timeout)


def _within_tolerance_read(setpoint: float, readback: float, tolerance: float) -> bool:
    return abs(setpoint - readback) < abs(tolerance)


class MovableWithTolerance(StandardMovable[float], StandardReadable):
    """Movable with a signal to configure the tolerance of when the device is done
    moving if it the readback and setpoint difference is within the tolerance.
    """

    def __init__(
        self,
        tolerance: SignalR[float],
        setpoint: SignalRW[float],
        readback: SignalR[float],
        name: str = "",
    ):
        # Use reference so sub classes still have flexibility to name signals to what
        # they want.
        self._setpoint_ref = Reference(setpoint)
        self._readback_ref = Reference(readback)
        self.within_tolerance = derived_signal_r(
            _within_tolerance_read,
            tolerance=tolerance,
            setpoint=setpoint,
            readback=readback,
        )
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> MovableWithToleranceLogic:
        return MovableWithToleranceLogic(
            readback=self._readback_ref(),
            setpoint=self._setpoint_ref(),
            within_tolerance=self.within_tolerance,
        )
