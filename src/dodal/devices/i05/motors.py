import asyncio
from math import radians

import numpy as np
from ophyd_async.core import derived_signal_rw

from dodal.devices.motors import (
    _AZIMUTH,
    _POLAR,
    _TILT,
    _X,
    _Y,
    _Z,
    XYZPolarAzimuthTiltStage,
)


class I05Goniometer(XYZPolarAzimuthTiltStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and tilt. This implementation extends to add perp and long coordinate transformation
    derived signals.
    """

    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        polar_infix: str = _POLAR,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
        rotation_angle_deg: float = 50,
        name: str = "",
    ):
        self.theta = radians(rotation_angle_deg)

        super().__init__(
            prefix,
            name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            polar_infix=polar_infix,
            azimuth_infix=azimuth_infix,
            tilt_infix=tilt_infix,
        )

        with self.add_children_as_readables():
            self.long = derived_signal_rw(
                self._read_long_calc,
                self._set_long_calc,
                x=self.x,
                y=self.y,
                theta=self.theta,
            )
            self.perp = derived_signal_rw(
                self._read_perp_calc,
                self._set_perp_calc,
                x=self.x,
                y=self.y,
                theta=self.theta,
            )

    def _rotation_matrix(self, theta) -> np.ndarray:
        c, s = np.cos(theta), np.sin(theta)
        return np.array([[c, s], [-s, c]])

    def _inverse_rotation_matrix(self, theta) -> np.ndarray:
        return self._rotation_matrix(theta).T

    def _read_long_calc(self, x: float, y: float, theta: float) -> float:
        vec = np.array([x, y])
        perp, long = self._rotation_matrix(theta) @ vec
        return long

    async def _set_long_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = self._read_perp_calc(x_pos, y_pos, self.theta)
        long = value

        vec_rot = np.array([perp, long])
        new_x_pos, new_y_pos = self._inverse_rotation_matrix(self.theta) @ vec_rot

        await asyncio.gather(self.x.set(new_x_pos), self.y.set(new_y_pos))

    def _read_perp_calc(self, x: float, y: float, theta: float) -> float:
        vec = np.array([x, y])
        perp, long = self._rotation_matrix(theta) @ vec
        return perp

    async def _set_perp_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )

        long = self._read_long_calc(x_pos, y_pos, self.theta)
        perp = value

        vec_rot = np.array([perp, long])
        new_x_pos, new_y_pos = self._inverse_rotation_matrix(self.theta) @ vec_rot

        await asyncio.gather(self.x.set(new_x_pos), self.y.set(new_y_pos))
