from dataclasses import dataclass
from functools import cached_property

from bluesky.protocols import Flyable, Preparable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    SignalRW,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    WatchableAsyncStatus,
    error_if_none,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from pydantic import BaseModel, Field

from dodal.devices.movable import MovableWithTolerance, MovableWithToleranceLogic


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
class HighFieldMagnetMovableLogic(MovableWithToleranceLogic):
    speed: SignalRW[float]
    acc_time: SignalRW[float]

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


class HighFieldMagnet(MovableWithTolerance, Flyable, Preparable):
    def __init__(
        self, prefix: str, field_tolerance: float = 0.01, name: str = ""
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.sweep_rate = epics_signal_rw(
                float,
                read_pv=prefix + "RBV:FIELDSWEEPRATE",
                write_pv=prefix + "SET:FIELDSWEEPRATE",
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
            self.tolerance = soft_signal_rw(float, initial_value=field_tolerance)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + "RBV:DEMANDFIELD")

        self.set_move = epics_signal_w(
            HighFieldMagnetStatus,
            write_pv=prefix + "SET:ACTIVITY",
        )
        self.user_setpoint = epics_signal_rw(
            float,
            read_pv=prefix + "RBV:SETPOINTFIELD",
            write_pv=prefix + "SET:SETPOINTFIELD",
        )
        self._set_success = True
        self._fly_info: FlyMagInfo | None = None
        self._fly_status: WatchableAsyncStatus | None = None

        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> HighFieldMagnetMovableLogic:
        return HighFieldMagnetMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.user_readback,
            within_tolerance=self.within_tolerance,
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
