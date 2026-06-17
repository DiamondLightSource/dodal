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
        # Don't use set_and_wait_for_other_value until we drop support for Python 3.11.
        # In Python 3.11 there appears to be a timing issue where, if within_tolerance
        # is already True (for example, because the current readback is close to the
        # current setpoint), the wait condition can be satisfied before the new setpoint
        # is applied. This can cause the move task to complete immediately instead of
        # waiting for the new target position to be reached.
        #
        # For now, set the setpoint first and then wait for within_tolerance to become
        # True for the newly requested position.
        await self.setpoint.set(new_position)
        await wait_for_value(self.within_tolerance, True, timeout)


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
