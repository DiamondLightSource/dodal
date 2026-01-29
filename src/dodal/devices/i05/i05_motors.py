import asyncio
from math import radians

from numpy import cos as c
from numpy import sin as s
from ophyd_async.core import derived_signal_rw

from dodal.devices.i05_shared.math import inverse_rotate, rotate
from dodal.devices.motors import (
    _AZIMUTH,
    _POLAR,
    _TILT,
    _X,
    _Y,
    _Z,
    XYZPolarAzimuthTiltStage,
)


def neg_s(x: float) -> float:
    return -s(x)


ROTATION_MATRIX = [[c, s], [neg_s, c]]


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

    def _read_perp_calc(self, x: float, y: float, angle_deg: float) -> float:
        new_x, new_y = rotate(radians(angle_deg), x, y, ROTATION_MATRIX)
        return new_x

    async def _set_perp_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = value
        long = self._read_long_calc(x_pos, y_pos, self.rotation_angle_deg)
        new_x, new_y = inverse_rotate(
            radians(self.rotation_angle_deg), perp, long, ROTATION_MATRIX
        )
        await asyncio.gather(self.x.set(new_x), self.y.set(new_y))

    def _read_long_calc(self, x: float, y: float, angle_deg: float) -> float:
        new_x, new_y = rotate(radians(angle_deg), x, y, ROTATION_MATRIX)
        return new_y

    async def _set_long_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = self._read_perp_calc(x_pos, y_pos, self.rotation_angle_deg)
        long = value
        new_x, new_y = inverse_rotate(
            radians(self.rotation_angle_deg), perp, long, ROTATION_MATRIX
        )
        await asyncio.gather(self.x.set(new_x), self.y.set(new_y))
