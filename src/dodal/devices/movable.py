from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    MovableLogic,
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    TimeoutCalculator,
    derived_signal_r,
    wait_for_value,
)


@dataclass
class MovableWithToleranceLogic(MovableLogic[float]):
    within_tolerance: SignalR[bool]

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        await self.setpoint.set(new_position, timeout=timeout())
        await wait_for_value(self.setpoint, new_position, timeout=timeout())
        # Once setpoint is at new position, we can check for tolerance signal to see if
        # true now as the within_tolerance window has updated to the new setpoint
        # position. Now it doesn't matter if motor steps are small or large.
        await wait_for_value(self.within_tolerance, True, timeout=timeout())


def _within_tolerance_read(setpoint: float, readback: float, tolerance: float) -> bool:
    return abs(setpoint - readback) < abs(tolerance)


class MovableWithTolerance(StandardMovable[float], StandardReadable):
    """Movable with a signal to configure the tolerance of when the device is done
    moving if it the readback and setpoint difference is within the tolerance.
    """

    tolerance: SignalR[float]
    user_setpoint: SignalRW[float]
    user_readback: SignalR[float]

    def __init__(
        self,
        name: str = "",
    ):
        self.within_tolerance = derived_signal_r(
            _within_tolerance_read,
            tolerance=self.tolerance,
            setpoint=self.user_setpoint,
            readback=self.user_readback,
        )
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> MovableWithToleranceLogic:
        return MovableWithToleranceLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            within_tolerance=self.within_tolerance,
        )
