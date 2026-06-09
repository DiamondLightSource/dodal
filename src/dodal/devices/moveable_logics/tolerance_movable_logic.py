from __future__ import annotations

from dataclasses import dataclass, field

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    MovableLogic,
    SignalR,
    SignalRW,
    derived_signal_r,
    set_and_wait_for_other_value,
)


@dataclass
class ToleranceMovableLogic(MovableLogic[float]):
    tolerance: SignalRW[float]
    speed: SignalRW[float]
    acc_time: SignalRW[float]
    within_tolerance: SignalR[bool] = field(init=False)

    def __post_init__(self) -> None:
        self.within_tolerance = derived_signal_r(
            raw_to_derived=self._within_tolerance,
            setpoint=self.setpoint,
            readback=self.readback,
            tolerance=self.tolerance,
        )

    def _within_tolerance(
        self,
        setpoint: float,
        readback: float,
        tolerance: float,
    ) -> bool:
        """Check if the readback is within the tolerance of the setpoint."""
        return abs(setpoint - readback) < abs(tolerance)

    async def stop(self):
        current_val = await self.readback.get_value()
        await self.setpoint.set(current_val)

    async def calculate_timeout(
        self, old_position: float, new_position: float
    ) -> float:

        try:
            timeout = (
                abs((new_position - old_position) / await self.speed.get_value())
                + 2 * await self.acc_time.get_value()
                + DEFAULT_TIMEOUT
            )
        except ZeroDivisionError as error:
            msg = "zero speed."
            raise ValueError(msg) from error
        return timeout

    async def move(self, new_position: float, timeout: float | None) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.setpoint,
            set_value=new_position,
            match_signal=self.within_tolerance,
            match_value=True,
            timeout=timeout,
        )
