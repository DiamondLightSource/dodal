"""Ophyd-async controller and scannable devices for the 4-magnet Halbach array on I10 RASOR."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.common.maths import AngleWithPhase
from dodal.devices.beamlines.i10.rasor.halbach.halbach_lut import HalbachLookupTable


@dataclass(frozen=True)
class HalbachSetpoint:
    """Target magnetic field strength and/or angle relative to the z-axis.

    If either `h_mt` or `field_angle_z_deg` is `None`, the controller preserves the
    current value of that coordinate.
    """

    h_mt: float | None = None
    field_angle_z_deg: float | None = None


class HalbachMagnetArrayController(StandardReadable, Movable[HalbachSetpoint]):
    """Controller for the 4-magnet Halbach array using a 2D lookup table."""

    def __init__(
        self,
        prefix: str,
        lut: HalbachLookupTable,
        m1_suffix: str = "MAG1:THETA",
        m2_suffix: str = "MAG2:THETA",
        m3_suffix: str = "MAG3:THETA",
        m4_suffix: str = "MAG4:THETA",
        waypoint_step_mt: float = 5.0,
        waypoint_step_deg: float = 5.0,
        name: str = "",
    ) -> None:
        self.lut = lut

        self._h_setpoint = soft_signal_rw(float, initial_value=0.0, units="mT")
        self._angle_setpoint = soft_signal_rw(float, initial_value=0.0, units="deg")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.waypoint_step_mt = soft_signal_rw(
                float, initial_value=float(waypoint_step_mt), units="mT"
            )
            self.waypoint_step_deg = soft_signal_rw(
                float, initial_value=float(waypoint_step_deg), units="deg"
            )

        with self.add_children_as_readables():
            self.m1 = Motor(prefix + m1_suffix)
            self.m2 = Motor(prefix + m2_suffix)
            self.m3 = Motor(prefix + m3_suffix)
            self.m4 = Motor(prefix + m4_suffix)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.field_strength = derived_signal_rw(
                raw_to_derived=self._get_field_strength,
                set_derived=self._set_field_strength,
                h_mt=self._h_setpoint,
                derived_units="mT",
            )
            self.field_angle = derived_signal_rw(
                raw_to_derived=self._get_field_angle,
                set_derived=self._set_field_angle,
                angle_deg=self._angle_setpoint,
                derived_units="deg",
            )
            # https://github.com/bluesky/ophyd-async/issues/1231
            self.field_strength._timeout = None  # noqa: SLF001
            self.field_angle._timeout = None  # noqa: SLF001

        super().__init__(name=name)

    @property
    def motors(self) -> tuple[Motor, Motor, Motor, Motor]:
        """Return the 4 underlying rotational motors in order (m1, m2, m3, m4)."""
        return (self.m1, self.m2, self.m3, self.m4)

    def _get_field_strength(self, h_mt: float) -> float:
        return h_mt

    def _get_field_angle(self, angle_deg: float) -> float:
        return angle_deg

    async def get_current_field_and_angle(self) -> tuple[float, float]:
        """Return the current `(h_mt, field_angle_z_deg)` setpoints."""
        h_cur, a_cur = await asyncio.gather(
            self._h_setpoint.get_value(),
            self._angle_setpoint.get_value(),
        )
        return float(h_cur), float(a_cur)

    async def _set_field_strength(self, h_mt: float) -> None:
        _, current_angle_deg = await self.get_current_field_and_angle()
        await self._move_to_field(float(h_mt), current_angle_deg)

    async def _set_field_angle(self, angle_deg: float) -> None:
        current_h_mt, _ = await self.get_current_field_and_angle()
        await self._move_to_field(current_h_mt, float(angle_deg))

    @AsyncStatus.wrap
    async def set(self, value: HalbachSetpoint) -> None:
        """Move all 4 Halbach motors to achieve the target `(H_mT, Field_Angle_Z_deg)`.

        If either `h_mt` or `field_angle_z_deg` is `None`, the current value of that
        coordinate is preserved.
        """
        req_h, req_angle = value.h_mt, value.field_angle_z_deg

        if req_h is None and req_angle is None:
            raise ValueError(
                "At least one of h_mt or field_angle_z_deg must be provided."
            )

        cur_h, cur_angle = await self.get_current_field_and_angle()
        target_h = float(req_h) if req_h is not None else cur_h
        target_angle = float(req_angle) if req_angle is not None else cur_angle
        await self._move_to_field(target_h, target_angle)

    @staticmethod
    def compute_shortest_path_targets(
        current_deg: np.ndarray, lut_target_deg: np.ndarray
    ) -> np.ndarray:
        """Map LUT target angles to the nearest angles relative to current_deg."""
        targets = np.empty(4, dtype=float)
        for k in range(4):
            current_angle = AngleWithPhase.wrap(float(current_deg[k]))
            targets[k] = current_angle.nearest_with_phase(
                float(lut_target_deg[k])
            ).unwrap()
        return targets

    async def calculate_waypoints(
        self,
        start_h_mt: float,
        start_angle_deg: float,
        target_h_mt: float,
        target_angle_deg: float,
    ) -> list[tuple[float, float]]:
        """Divide a field move into h_mt, angle_deg waypoints if configured."""
        step_mt, step_deg = await asyncio.gather(
            self.waypoint_step_mt.get_value(),
            self.waypoint_step_deg.get_value(),
        )
        n_steps = 1
        if step_mt > 0:
            n_h = math.ceil(abs(target_h_mt - start_h_mt) / step_mt)
            n_steps = max(n_steps, n_h)
        if step_deg > 0:
            n_a = math.ceil(abs(target_angle_deg - start_angle_deg) / step_deg)
            n_steps = max(n_steps, n_a)

        if n_steps <= 1:
            return [(target_h_mt, target_angle_deg)]

        h_pts = np.linspace(start_h_mt, target_h_mt, n_steps + 1)[1:]
        a_pts = np.linspace(start_angle_deg, target_angle_deg, n_steps + 1)[1:]
        return [(float(h), float(a)) for h, a in zip(h_pts, a_pts, strict=True)]

    async def _move_to_field(self, target_h_mt: float, target_angle_deg: float) -> None:
        self.lut.interpolate(target_h_mt, target_angle_deg)

        start_h, start_angle = await self.get_current_field_and_angle()
        waypoints = await self.calculate_waypoints(
            start_h_mt=start_h,
            start_angle_deg=start_angle,
            target_h_mt=target_h_mt,
            target_angle_deg=target_angle_deg,
        )

        ref_deg = np.array(
            await asyncio.gather(*(m.user_readback.get_value() for m in self.motors)),
            dtype=float,
        )

        for wp_h, wp_angle in waypoints:
            lut_deg = self.lut.interpolate(wp_h, wp_angle)
            target_deg = self.compute_shortest_path_targets(ref_deg, lut_deg)
            await asyncio.gather(
                *(
                    motor.set(float(pos))
                    for motor, pos in zip(self.motors, target_deg, strict=True)
                )
            )
            await asyncio.gather(
                self._h_setpoint.set(wp_h),
                self._angle_setpoint.set(wp_angle),
            )
            ref_deg = target_deg


class HalbachField(StandardReadable, Movable[float]):
    """Device for magnetic field strength (`H` in mT).

    Moving HalbachField keeps angle unchanged.
    """

    def __init__(
        self, controller: HalbachMagnetArrayController, name: str = ""
    ) -> None:
        self.field_strength = Reference(controller.field_strength)
        super().__init__(name=name)
        self.add_readables(
            [self.field_strength()], StandardReadableFormat.HINTED_SIGNAL
        )

    @AsyncStatus.wrap
    async def set(self, value: float, timeout: float | None = None) -> None:
        await self.field_strength().set(float(value), timeout=timeout)


class HalbachAngle(StandardReadable, Movable[float]):
    """Device for magnetic field angle .

    Moving HalbachAngle keeps field unchanged.
    """

    def __init__(
        self, controller: HalbachMagnetArrayController, name: str = ""
    ) -> None:
        self.field_angle = Reference(controller.field_angle)
        super().__init__(name=name)
        self.add_readables([self.field_angle()], StandardReadableFormat.HINTED_SIGNAL)

    @AsyncStatus.wrap
    async def set(self, value: float, timeout: float | None = None) -> None:
        await self.field_angle().set(float(value), timeout=timeout)
