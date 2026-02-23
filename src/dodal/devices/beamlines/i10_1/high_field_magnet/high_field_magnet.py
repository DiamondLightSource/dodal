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
    FlyMotorInfo,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    WatchableAsyncStatus,
    WatcherUpdate,
    derived_signal_r,
    observe_value,
    set_and_wait_for_other_value,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w


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
            self.sweeprate = epics_signal_rw(
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

        self._fly_info: FlyMotorInfo | None = None

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
            sweeprate,
            ramp_up_time,
        ) = await asyncio.gather(
            self.user_setpoint.get_value(),
            self.sweeprate.get_value(),
            self.ramp_up_time.get_value(),
        )

        try:
            timeout = (
                abs((new_position - old_position) / sweeprate)
                + 2 * ramp_up_time
                + DEFAULT_TIMEOUT
            )
        except ZeroDivisionError as error:
            msg = "Mover has zero velocity"
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
            raise RuntimeError("Field was stopped")

    # @AsyncStatus.wrap
    # async def prepare(self, value: FlyMotorInfo):
    #     """Move to the beginning of a suitable run-up distance ready for a fly scan."""
    #     self._fly_info = value

    #     # Velocity, at which motor travels from start_position to end_position, in motor
    #     # egu/s.
    #     max_speed, egu = await asyncio.gather(
    #         self.max_velocity.get_value(), self.motor_egu.get_value()
    #     )
    #     if abs(value.velocity) > max_speed:
    #         raise MotorLimitsError(
    #             f"Velocity {abs(value.velocity)} {egu}/s was requested for a motor "
    #             f" with max speed of {max_speed} {egu}/s"
    #         )

    #     acceleration_time = await self.ramp_up_time.get_value()
    #     ramp_up_start_pos = value.ramp_up_start_pos(acceleration_time)
    #     ramp_down_end_pos = value.ramp_down_end_pos(acceleration_time)

    #     await self.check_motor_limit(ramp_up_start_pos, ramp_down_end_pos)

    #     # move to prepare position at maximum velocity
    #     await self.velocity.set(abs(max_speed))
    #     await self.set(ramp_up_start_pos)

    #     # Set velocity we will be using for the fly scan
    #     await self.velocity.set(abs(value.velocity))

    # @AsyncStatus.wrap
    # async def kickoff(self):
    #     """Begin moving motor from prepared position to final position."""
    #     fly_info = error_if_none(
    #         self._fly_info, "Motor must be prepared before attempting to kickoff"
    #     )

    #     acceleration_time = await self.acceleration_time.get_value()
    #     self._fly_status = self.set(
    #         fly_info.ramp_down_end_pos(acceleration_time),
    #         timeout=fly_info.timeout,
    #     )

    # def complete(self) -> WatchableAsyncStatus:
    #     """Mark as complete once motor reaches completed position."""
    #     fly_status = error_if_none(self._fly_status, "kickoff not called")
    #     return fly_status
