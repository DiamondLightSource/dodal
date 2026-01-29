import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from math import radians

import numpy as np
from numpy import cos as c
from numpy import sin as s
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


@dataclass
class Vector2D:
    """
    Helper class that can perform rotations on x and y. It is configured with a matrix
    of callables so this can be used for any kind of rotation.

    from numpy import cos as c
    from numpy import sin as s

    def neg_s(x: float) -> float:
        return -s(x)

    ROTATION_MATRIX = [[c, s], [neg_s, c]]
    x, y = 1, 5

    vec = Vector2D(x, y, ROTATION_MATRIX)
    new_vec = vec.rotate_deg(45)
    new_x = new_vec.x
    new_y = new_vec.y
    """

    x: float
    y: float
    callable_rotation_matrix: list[list[Callable[[float], float]]]

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @classmethod
    def from_array(
        cls,
        arr: np.ndarray,
        callable_rotation_matrix: list[list[Callable[[float], float]]],
    ) -> "Vector2D":
        return cls(
            x=arr[0], y=arr[1], callable_rotation_matrix=callable_rotation_matrix
        )

    def _rotation_matrix(self, theta) -> np.ndarray:
        return np.array(
            [
                [fn(theta) for fn in row_functions]
                for row_functions in self.callable_rotation_matrix
            ]
        )

    def _inverse_rotation_matrix(self, theta) -> np.ndarray:
        return self._rotation_matrix(theta).T

    def rotate_deg(self, angle_deg: float) -> "Vector2D":
        return self.rotate(radians(angle_deg))

    def rotate(self, theta: float) -> "Vector2D":
        rotated = self._rotation_matrix(theta) @ self.to_array()
        return Vector2D.from_array(rotated, self.callable_rotation_matrix)

    def inverse_rotate_deg(self, angle_deg: float) -> "Vector2D":
        return self.inverse_rotate(radians(angle_deg))

    def inverse_rotate(self, theta: float) -> "Vector2D":
        rotated = self._inverse_rotation_matrix(theta) @ self.to_array()
        return Vector2D.from_array(rotated, self.callable_rotation_matrix)

    def __repr__(self):
        return f"Vector2D(x={self.x}, y={self.y})"


def neg_s(x: float) -> float:
    return -s(x)


ROTATION_MATRIX = rotation_matrix = [[c, s], [neg_s, c]]


class I05Goniometer(XYZPolarAzimuthTiltStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and tilt. This implementation extends to add perp and long rotations as derived
    signals at a configured angle (default 50 degrees.)
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
        rotation_angle_deg: float = 50.0,
        name: str = "",
    ):
        self.rotation_angle_deg = rotation_angle_deg

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
                angle_deg=self.rotation_angle_deg,
            )
            self.perp = derived_signal_rw(
                self._read_perp_calc,
                self._set_perp_calc,
                x=self.x,
                y=self.y,
                angle_deg=self.rotation_angle_deg,
            )

    def _read_long_calc(self, x: float, y: float, angle_deg: float) -> float:
        vec = Vector2D(x, y, ROTATION_MATRIX)
        return vec.rotate_deg(angle_deg).y

    async def _set_long_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = self._read_perp_calc(x_pos, y_pos, self.rotation_angle_deg)
        vec = Vector2D(perp, value, ROTATION_MATRIX)
        new_pos = vec.inverse_rotate_deg(self.rotation_angle_deg)

        await asyncio.gather(self.x.set(new_pos.x), self.y.set(new_pos.y))

    def _read_perp_calc(self, x: float, y: float, angle_deg: float) -> float:
        vec = Vector2D(x, y, ROTATION_MATRIX)
        return vec.rotate_deg(angle_deg).x

    async def _set_perp_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        long = self._read_long_calc(x_pos, y_pos, self.rotation_angle_deg)
        vec = Vector2D(value, long, ROTATION_MATRIX)
        new_pos = vec.inverse_rotate_deg(self.rotation_angle_deg)

        await asyncio.gather(self.x.set(new_pos.x), self.y.set(new_pos.y))
