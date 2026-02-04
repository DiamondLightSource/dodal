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

from dodal.devices.motors import (
    _AZIMUTH,
    _TILT,
    _X,
    _Y,
    _Z,
    XYZAzimuthTiltPolarStage,
    XYZAzimuthTiltStage,
    create_rotational_ij_component_signals,
)


class I21XYZAzimuthTiltPolarStage(XYZAzimuthTiltPolarStage):
    """Note: I21 uses the following pv to variable
    - PV AZIMUTH but calls the variable phi.
    - PV TILT but calls variable chi.
    - PV RZ but calls it th (theta). Have used standard class in hopes
    We can try  topersuade i21 to use the standard variable names going forward to
    align with other beamlines and not alias variables.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
        polar_infix: str = "RZ",
    ):
        super().__init__(
            prefix,
            name,
            x_infix,
            y_infix,
            z_infix,
            azimuth_infix,
            tilt_infix,
            polar_infix,
        )

        with self.add_children_as_readables():
            # Parallel and Perpendicular
            self.para, self.perp = create_rotational_ij_component_signals(
                i_read=self.x.user_readback,
                j_read=self.y.user_readback,
                i_write=self.x,
                j_write=self.y,
                angle_deg=self.polar.user_readback,
                clockwise_frame=False,
            )


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


def toolpoint_to_xyz(
    u: float,
    v: float,
    w: float,
    tilt_deg: float,
    azimuth_deg: float,
    zero: tuple[float, float, float],
) -> tuple[float, float, float]:
    rotation = toolpoint_rotation_matrix(tilt_deg, azimuth_deg)
    tool = np.array([u, v, w])
    offset = np.array(zero)
    xyz = offset + rotation @ tool
    return tuple(xyz.astype(float))


def xyz_to_toolpoint(
    x: float,
    y: float,
    z: float,
    tilt_deg: float,
    azimuth_deg: float,
    zero: tuple[float, float, float],
) -> tuple[float, float, float]:
    rotation = toolpoint_rotation_matrix(tilt_deg, azimuth_deg)
    xyz = np.array([x, y, z])
    offset = np.array(zero)

    tool = rotation.T @ (xyz - offset)
    return tuple(tool.astype(float))


AXES_ZERO = (5.667, 0.2408, 1.221)


@dataclass(frozen=True)
class MotorPositions:
    x: float
    y: float
    z: float
    tilt: float
    azimuth: float


class ToolPointMotion(StandardReadable, Movable):
    def __init__(
        self,
        smp: XYZAzimuthTiltStage,
        zero: tuple[float, float, float] = AXES_ZERO,
        name: str = "",
    ):
        self.smp_ref = Reference(smp)
        self._zero = zero

        with self.add_children_as_readables():
            self.u, self.v, self.w = self._create_uvws()

        super().__init__(name=name)

    async def _read_motor_positions(self) -> MotorPositions:
        x, y, z, tilt, azimuth = await asyncio.gather(
            self.smp_ref().x.user_readback.get_value(),
            self.smp_ref().y.user_readback.get_value(),
            self.smp_ref().z.user_readback.get_value(),
            self.smp_ref().tilt.user_readback.get_value(),
            self.smp_ref().azimuth.user_readback.get_value(),
        )
        return MotorPositions(x, y, z, tilt, azimuth)

    async def _check_motor_limits(
        self, start: MotorPositions, end: MotorPositions
    ) -> None:
        await asyncio.gather(
            self.smp_ref().x.check_motor_limit(start.x, end.x),
            self.smp_ref().y.check_motor_limit(start.y, end.y),
            self.smp_ref().z.check_motor_limit(start.z, end.z),
            self.smp_ref().tilt.check_motor_limit(start.tilt, end.tilt),
            self.smp_ref().azimuth.check_motor_limit(start.azimuth, end.azimuth),
        )

    def _toolpoint_to_motor_positions(
        self, u: float, v: float, w: float, tilt: float, azimuth: float
    ) -> MotorPositions:
        x, y, z = toolpoint_to_xyz(u, v, w, tilt, azimuth, self._zero)
        return MotorPositions(
            x=x,
            y=y,
            z=z,
            tilt=tilt,
            azimuth=azimuth,
        )

    async def _read_all(self) -> tuple[float, float, float, float, float]:
        pos = await self._read_motor_positions()
        u, v, w = xyz_to_toolpoint(
            pos.x,
            pos.y,
            pos.z,
            pos.tilt,
            pos.azimuth,
            self._zero,
        )
        return u, v, w, pos.tilt, pos.azimuth

    async def _write_all(
        self, u: float, v: float, w: float, tilt: float, azimuth: float
    ) -> None:
        start = await self._read_motor_positions()
        end = self._toolpoint_to_motor_positions(u, v, w, tilt, azimuth)

        await self._check_motor_limits(start, end)

        await asyncio.gather(
            self.smp_ref().x.set(end.x),
            self.smp_ref().y.set(end.y),
            self.smp_ref().z.set(end.z),
            self.smp_ref().tilt.set(end.tilt),
            self.smp_ref().azimuth.set(end.azimuth),
        )

    def _create_uvws(self) -> tuple[SignalRW[float], SignalRW[float], SignalRW[float]]:
        def read_u(x: float, y: float, z: float, tilt: float, azimuth: float) -> float:
            return xyz_to_toolpoint(x, y, z, tilt, azimuth, self._zero)[0]

        async def set_u(value: float) -> None:
            u, v, w, tilt, azimuth = await self._read_all()
            await self._write_all(value, v, w, tilt, azimuth)

        def read_v(x: float, y: float, z: float, tilt: float, azimuth: float) -> float:
            return xyz_to_toolpoint(x, y, z, tilt, azimuth, self._zero)[1]

        async def set_v(value: float) -> None:
            u, v, w, tilt, azimuth = await self._read_all()
            await self._write_all(u, value, w, tilt, azimuth)

        def read_w(x: float, y: float, z: float, tilt: float, azimuth: float) -> float:
            return xyz_to_toolpoint(x, y, z, tilt, azimuth, self._zero)[2]

        async def set_w(value: float) -> None:
            u, v, w, tilt, azimuth = await self._read_all()
            await self._write_all(u, v, value, tilt, azimuth)

        u = derived_signal_rw(
            read_u,
            set_u,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt=self.smp_ref().tilt,
            azimuth=self.smp_ref().azimuth,
        )
        v = derived_signal_rw(
            read_v,
            set_v,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt=self.smp_ref().tilt,
            azimuth=self.smp_ref().azimuth,
        )
        w = derived_signal_rw(
            read_w,
            set_w,
            x=self.smp_ref().x,
            y=self.smp_ref().y,
            z=self.smp_ref().z,
            tilt=self.smp_ref().tilt,
            azimuth=self.smp_ref().azimuth,
        )
        return u, v, w

    @AsyncStatus.wrap
    async def set(self, value: MotorPositions):
        await self._write_all(value.x, value.y, value.z, value.tilt, value.azimuth)
