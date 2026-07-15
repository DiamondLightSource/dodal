from dataclasses import dataclass

from ophyd_async.core import (
    MovableLogic,
    SignalR,
    TimeoutCalculator,
    set_and_wait_for_other_value,
)


@dataclass
class MovableWithToleranceLogic(MovableLogic[float]):
    tolerance: SignalR[float]

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        tolerance = await self.tolerance.get_value()
        await set_and_wait_for_other_value(
            self.setpoint,
            new_position,
            self.readback,
            lambda current_position: is_within_tolerance(
                new_position, current_position, tolerance
            ),
            timeout=timeout(),
        )


def is_within_tolerance(setpoint: float, readback: float, tolerance: float) -> bool:
    return abs(setpoint - readback) < abs(tolerance)
