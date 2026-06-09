from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from bluesky.protocols import (
    Flyable,
    Preparable,
)
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    MovableLogic,
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    WatchableAsyncStatus,
    derived_signal_r,
    error_if_none,
    set_and_wait_for_other_value,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from pydantic import BaseModel, Field


class HighFieldMangetSweepTypes(StrictEnum):
    FAST = "Fast"
    SLOW = "Slow"


class HighFieldMagnetStatus(SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMP = "Clamp"


class HighFieldMagnetStatusRBV(SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMPED = "Clamped"


class FlyMagInfo(BaseModel):
    """Minimal set of information required to fly high field magnet."""

    start_position: float = Field(frozen=True)

    end_position: float = Field(frozen=True)

    sweep_rate: float = Field(frozen=True, gt=0)


@dataclass
class ToleranceLogic(MovableLogic[float]):
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
            msg = "Magnet has zero sweep_rate."
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


class HighFieldMagnet(
    StandardMovable,
    StandardReadable,
    Flyable,
    Preparable,
):
    def __init__(
        self, prefix: str, field_tolerance: float = 0.01, name: str = ""
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.sweep_rate = epics_signal_rw(
                float,
                read_pv=prefix + "RBV:FIELDsweep_rate",
                write_pv=prefix + "SET:FIELDsweep_rate",
            )
            self.sweep_type = epics_signal_rw(
                HighFieldMangetSweepTypes,
                read_pv=prefix + "STS:SWEEPMODE:TYPE",
                write_pv=prefix + "SET:SWEEPMODE:TYPE",
            )
            self.set_move_readback = epics_signal_r(
                HighFieldMagnetStatusRBV,
                read_pv=prefix + "STS:ACTIVITY",
            )
            self.ramp_up_time = soft_signal_rw(datatype=float, initial_value=1.0)
            self.field_tolerance = soft_signal_rw(float, initial_value=field_tolerance)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + "RBV:DEMANDFIELD")

        self.set_mode = epics_signal_w(
            HighFieldMagnetStatus,
            write_pv=prefix + "SET:ACTIVITY",
        )
        self.user_setpoint = epics_signal_rw(
            float,
            read_pv=prefix + "RBV:SETPOINTFIELD",
            write_pv=prefix + "SET:SETPOINTFIELD",
        )

        self._fly_info: FlyMagInfo | None = None

        self._fly_status: WatchableAsyncStatus | None = None

        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> MovableLogic:
        return ToleranceLogic(
            setpoint=self.user_setpoint,
            readback=self.user_readback,
            tolerance=self.field_tolerance,
            speed=self.sweep_rate,
            acc_time=self.ramp_up_time,
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMagInfo) -> None:
        """Move to the beginning of a suitable run-up distance ready for a fly scan."""
        self._fly_info = value

        await self.set(value.start_position)

        await self.sweep_rate.set(abs(value.sweep_rate))

    @AsyncStatus.wrap
    async def kickoff(self):
        fly_info = error_if_none(
            self._fly_info, "Magnet must be prepared before attempting to kickoff"
        )

        self._fly_status = self.set(fly_info.end_position)

    def complete(self) -> WatchableAsyncStatus:
        fly_status = error_if_none(self._fly_status, "kickoff not called")
        return fly_status
