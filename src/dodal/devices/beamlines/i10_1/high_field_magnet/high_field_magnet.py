from __future__ import annotations

from functools import cached_property

import ophyd_async.core
from bluesky.protocols import (
    Flyable,
    Preparable,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from pydantic import BaseModel, Field

from dodal.devices.moveable_logics import ToleranceMovableLogic


class HighFieldMangetSweepTypes(ophyd_async.core.StrictEnum):
    FAST = "Fast"
    SLOW = "Slow"


class HighFieldMagnetStatus(ophyd_async.core.SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMP = "Clamp"


class HighFieldMagnetStatusRBV(ophyd_async.core.SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMPED = "Clamped"


class FlyMagInfo(BaseModel):
    """Minimal set of information required to fly high field magnet."""

    start_position: float = Field(frozen=True)

    end_position: float = Field(frozen=True)

    sweep_rate: float = Field(frozen=True, gt=0)


class HighFieldMagnet(
    ophyd_async.core.StandardMovable,
    ophyd_async.core.StandardReadable,
    Flyable,
    Preparable,
):
    def __init__(
        self, prefix: str, field_tolerance: float = 0.01, name: str = ""
    ) -> None:
        with self.add_children_as_readables(
            ophyd_async.core.StandardReadableFormat.CONFIG_SIGNAL
        ):
            self.sweep_rate = epics_signal_rw(
                float,
                read_pv=prefix + "RBV:FIELDsweeprate",
                write_pv=prefix + "SET:FIELDsweeprate",
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
            self.ramp_up_time = ophyd_async.core.soft_signal_rw(
                datatype=float, initial_value=1.0
            )
            self.field_tolerance = ophyd_async.core.soft_signal_rw(
                float, initial_value=field_tolerance
            )
        with self.add_children_as_readables(
            ophyd_async.core.StandardReadableFormat.HINTED_SIGNAL
        ):
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

        self._fly_status: ophyd_async.core.WatchableAsyncStatus | None = None

        super().__init__(name=name)

    @cached_property
    def movable_logic(self) -> ophyd_async.core.MovableLogic:
        return ToleranceMovableLogic(
            setpoint=self.user_setpoint,
            readback=self.user_readback,
            tolerance=self.field_tolerance,
            speed=self.sweep_rate,
            acc_time=self.ramp_up_time,
        )

    @ophyd_async.core.AsyncStatus.wrap
    async def prepare(self, value: FlyMagInfo) -> None:
        """Move to the beginning of a suitable run-up distance ready for a fly scan."""
        self._fly_info = value

        await self.set(value.start_position)

        await self.sweep_rate.set(abs(value.sweep_rate))

    @ophyd_async.core.AsyncStatus.wrap
    async def kickoff(self):
        fly_info = ophyd_async.core.error_if_none(
            self._fly_info, "Magnet must be prepared before attempting to kickoff"
        )

        self._fly_status = self.set(fly_info.end_position)

    def complete(self) -> ophyd_async.core.WatchableAsyncStatus:
        fly_status = ophyd_async.core.error_if_none(
            self._fly_status, "kickoff not called"
        )
        return fly_status
