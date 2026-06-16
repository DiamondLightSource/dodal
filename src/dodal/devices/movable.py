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
    set_and_wait_for_other_value,
)


@dataclass
class MovableWithToleranceLogic(MovableLogic[float]):
    within_tolerance: SignalR[bool]

    async def move(self, new_position: float, timeout: float | None) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.setpoint,
            set_value=new_position,
            match_signal=self.within_tolerance,
            match_value=True,
            timeout=timeout,
        )


def _within_tolerance_read(setpoint: float, readback: float, tolerance: float) -> bool:
    return abs(setpoint - readback) < abs(tolerance)


class MovableWithTolerance(StandardMovable[float], StandardReadable):
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
