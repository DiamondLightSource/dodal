from __future__ import annotations

import asyncio

from bluesky.protocols import (
    Flyable,
    Locatable,
    Location,
    Preparable,
    Reading,
    Stoppable,
    Subscribable,
)
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Callback,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    WatchableAsyncStatus,
    WatcherUpdate,
    derived_signal_r,
    error_if_none,
    observe_value,
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
    """Minimal set of information required to fly a high field magnet."""

    start_position: float = Field(frozen=True)

    end_position: float = Field(frozen=True)

    sweep_rate: float = Field(frozen=True, gt=0)


class HighFieldMagnet(
    StandardReadable,
    Locatable[float],
    Stoppable,
    Flyable,
    Preparable,
    Subscribable[float],
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

        self.set_move = epics_signal_w(
            HighFieldMagnetStatus,
            write_pv=prefix + "SET:ACTIVITY",
        )
        self.user_setpoint = epics_signal_rw(
            float,
            read_pv=prefix + "RBV:SETPOINTFIELD",
            write_pv=prefix + "SET:SETPOINTFIELD",
        )

        self.within_tolerance = derived_signal_r(
            raw_to_derived=self._within_tolerance,
            setpoint=self.user_setpoint,
            readback=self.user_readback,
            tolerance=self.field_tolerance,
        )

        self._set_success = True

        self._fly_info: FlyMagInfo | None = None

        self._fly_status: WatchableAsyncStatus | None = None

        super().__init__(name=name)

    def _within_tolerance(
        self, setpoint: float, readback: float, tolerance: float
    ) -> bool:
        """Check if the readback is within the tolerance of the setpoint."""
        return abs(setpoint - readback) < abs(tolerance)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        super().set_name(name, child_name_separator=child_name_separator)
        self.user_readback.set_name(name)

    async def locate(self) -> Location[float]:
        setpoint, readback = await asyncio.gather(
            self.user_setpoint.get_value(), self.user_readback.get_value()
        )
        return Location(setpoint=setpoint, readback=readback)

    async def stop(self, success=False):
        self._set_success = success
        await self.user_readback.get_value()
        await self.user_setpoint.set(await self.user_readback.get_value(), wait=False)

    def subscribe_reading(self, function: Callback[dict[str, Reading[float]]]) -> None:
        self.user_readback.subscribe_reading(function)

    subscribe = subscribe_reading

    def clear_sub(self, function: Callback[dict[str, Reading[float]]]) -> None:
        """Unsubscribe."""
        self.user_readback.clear_sub(function)

    @WatchableAsyncStatus.wrap
    async def set(
        self,
        new_position: float,
    ):
        self._set_success = True
        (
            old_position,
            sweep_rate,
            ramp_up_time,
        ) = await asyncio.gather(
            self.user_readback.get_value(),
            self.sweep_rate.get_value(),
            self.ramp_up_time.get_value(),
        )

        try:
            timeout = (
                abs((new_position - old_position) / sweep_rate)
                + 2 * ramp_up_time
                + DEFAULT_TIMEOUT
            )
        except ZeroDivisionError as error:
            msg = "Magnet has zero sweep_rate."
            raise ValueError(msg) from error

        move_status = AsyncStatus(
            set_and_wait_for_other_value(
                set_signal=self.user_setpoint,
                set_value=new_position,
                match_signal=self.within_tolerance,
                match_value=True,
                timeout=timeout,
            )
        )
        async for current_position in observe_value(
            self.user_readback, done_status=move_status
        ):
            yield WatcherUpdate(
                current=current_position,
                initial=old_position,
                target=new_position,
                name=self.name,
            )
        if not self._set_success:
            raise RuntimeError("Field changewas stopped")

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
