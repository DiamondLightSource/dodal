import asyncio
from dataclasses import dataclass
from math import cos, radians, sin

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    SignalRW,
    StandardReadable,
    derived_signal_rw,
)

from dodal.devices.motors import XYZAzimuthTiltStage

DEFAULT_AXES_ZERO = (5.667, 0.2408, 1.221)


def toolpoint_rotation_matrix(tilt_deg: float, azimuth_deg: float) -> np.ndarray:
    tilt = radians(tilt_deg)
    azimuth = radians(azimuth_deg)

    return np.array(
        [
            [cos(tilt), sin(tilt) * sin(azimuth), sin(tilt) * cos(azimuth)],
            [0.0, cos(azimuth), -sin(azimuth)],
            [-sin(tilt), cos(tilt) * sin(azimuth), cos(tilt) * cos(azimuth)],
        ]
    )


@dataclass(kw_only=True)
class AngleMotorPositions:
    tilt_deg: float
    azimuth_deg: float


@dataclass(kw_only=True)
class UVWMotorPositions(AngleMotorPositions):
    u: float
    v: float
    w: float


@dataclass(kw_only=True)
class XYZMotorPositions(AngleMotorPositions):
    x: float
    y: float
    z: float


def uvw_to_xyz(
    pos: UVWMotorPositions,
    zero: tuple[float, float, float],
) -> XYZMotorPositions:
    rotation = toolpoint_rotation_matrix(pos.tilt_deg, pos.azimuth_deg)
    uvw = np.array([pos.u, pos.v, pos.w])
    offset = np.array(zero)
    xyz = offset + rotation @ uvw
    x, y, z = xyz
    return XYZMotorPositions(
        x=x, y=y, z=z, tilt_deg=pos.tilt_deg, azimuth_deg=pos.azimuth_deg
    )


def xyz_to_uvw(
    pos: XYZMotorPositions,
    zero: tuple[float, float, float],
) -> UVWMotorPositions:
    rotation = toolpoint_rotation_matrix(pos.tilt_deg, pos.azimuth_deg)
    xyz = np.array([pos.x, pos.y, pos.z])
    offset = np.array(zero)

    tool = rotation.T @ (xyz - offset)
    u, v, w = tool
    return UVWMotorPositions(
        u=u, v=v, w=w, tilt_deg=pos.tilt_deg, azimuth_deg=pos.azimuth_deg
    )


class ToolPointMotion(StandardReadable, Movable):
    """Virtual manipulator translations of the sample stage. It is mounted on top
    of the diffractometer and circles tilt and azimuth angles. It defines three virtual
    axes u, v, and w as signals.
    """

    def __init__(
        self,
        smp: XYZAzimuthTiltStage,
        zero: tuple[float, float, float] = DEFAULT_AXES_ZERO,
        name: str = "",
    ):
        self.smp_ref = Reference(smp)
        self._zero = zero

        with self.add_children_as_readables():
            self.u, self.v, self.w = self._create_uvws()

        self.add_readables([smp])

        super().__init__(name=name)

    async def check_motor_limits(
        self, start: XYZMotorPositions, end: XYZMotorPositions
    ) -> None:
        await asyncio.gather(
            self.smp_ref().x.check_motor_limit(start.x, end.x),
            self.smp_ref().y.check_motor_limit(start.y, end.y),
            self.smp_ref().z.check_motor_limit(start.z, end.z),
            self.smp_ref().tilt.check_motor_limit(start.tilt_deg, end.tilt_deg),
            self.smp_ref().azimuth.check_motor_limit(
                start.azimuth_deg, end.azimuth_deg
            ),
        )

    async def _get_real_motor_positions(
        self,
    ) -> XYZMotorPositions:
        x, y, z, tilt, azimuth = await asyncio.gather(
            self.smp_ref().x.user_readback.get_value(),
            self.smp_ref().y.user_readback.get_value(),
            self.smp_ref().z.user_readback.get_value(),
            self.smp_ref().tilt.user_readback.get_value(),
            self.smp_ref().azimuth.user_readback.get_value(),
        )
        return XYZMotorPositions(x=x, y=y, z=z, tilt_deg=tilt, azimuth_deg=azimuth)

    async def _read_all_uvw(self) -> UVWMotorPositions:
        xyz_pos = await self._get_real_motor_positions()
        uvw_pos = xyz_to_uvw(xyz_pos, zero=self._zero)
        return uvw_pos

    async def _write_all_uvw(self, uvw_pos: UVWMotorPositions) -> None:
        xyz_start = await self._get_real_motor_positions()
        xyz_end = uvw_to_xyz(uvw_pos, self._zero)

        await self.check_motor_limits(xyz_start, xyz_end)
        await asyncio.gather(
            self.smp_ref().x.set(xyz_end.x),
            self.smp_ref().y.set(xyz_end.y),
            self.smp_ref().z.set(xyz_end.z),
            self.smp_ref().tilt.set(xyz_end.tilt_deg),
            self.smp_ref().azimuth.set(xyz_end.azimuth_deg),
        )

    def _create_uvws(self) -> tuple[SignalRW[float], SignalRW[float], SignalRW[float]]:
        def read_u(
            x: float, y: float, z: float, tilt_deg: float, azimuth_deg: float
        ) -> float:
            pos = XYZMotorPositions(
                x=x, y=y, z=z, tilt_deg=tilt_deg, azimuth_deg=azimuth_deg
            )
            return float(xyz_to_uvw(pos, self._zero).u)

        async def set_u(value: float) -> None:
            uvw_pos = await self._read_all_uvw()
            uvw_pos.u = value
            await self._write_all_uvw(uvw_pos)

        def read_v(
            x: float, y: float, z: float, tilt_deg: float, azimuth_deg: float
        ) -> float:
            pos = XYZMotorPositions(
                x=x, y=y, z=z, tilt_deg=tilt_deg, azimuth_deg=azimuth_deg
            )
            return float(xyz_to_uvw(pos, self._zero).v)

        async def set_v(value: float) -> None:
            uvw_pos = await self._read_all_uvw()
            uvw_pos.v = value
            await self._write_all_uvw(uvw_pos)

        def read_w(
            x: float, y: float, z: float, tilt_deg: float, azimuth_deg: float
        ) -> float:
            pos = XYZMotorPositions(
                x=x, y=y, z=z, tilt_deg=tilt_deg, azimuth_deg=azimuth_deg
            )
            return float(xyz_to_uvw(pos, self._zero).w)

        async def set_w(value: float) -> None:
            uvw_pos = await self._read_all_uvw()
            uvw_pos.w = value
            await self._write_all_uvw(uvw_pos)

        u = derived_signal_rw(
            read_u,
            set_u,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt_deg=self.smp_ref().tilt,
            azimuth_deg=self.smp_ref().azimuth,
        )
        v = derived_signal_rw(
            read_v,
            set_v,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt_deg=self.smp_ref().tilt,
            azimuth_deg=self.smp_ref().azimuth,
        )
        w = derived_signal_rw(
            read_w,
            set_w,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt_deg=self.smp_ref().tilt,
            azimuth_deg=self.smp_ref().azimuth,
        )
        return u, v, w

    @AsyncStatus.wrap
    async def set(self, value: UVWMotorPositions):
        await self._write_all_uvw(value)
