import asyncio
from math import cos, radians, sin

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

    def _read_long_calc(self, x: float, y: float, theta: float) -> float:
        return y * cos(theta) - x * sin(theta)

    async def _set_long_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(), self.y.user_readback.get_value()
        )
        perp = self._read_perp_calc(x_pos, y_pos, self.theta)
        long = value

        new_x_pos = -1 * long * sin(self.theta) + perp * cos(self.theta)
        new_y_pos = long * cos(self.theta) + perp * sin(self.theta)

        await asyncio.gather(self.x.set(new_x_pos), self.y.set(new_y_pos))

    def _read_perp_calc(self, x: float, y: float, theta: float) -> float:
        return y * sin(theta) + x * cos(theta)

    async def _set_perp_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(), self.y.user_readback.get_value()
        )

        long = self._read_long_calc(x_pos, y_pos, self.theta)
        perp = value

        new_x_pos = -1 * long * sin(self.theta) + perp * cos(self.theta)
        new_y_pos = long * cos(self.theta) + perp * sin(self.theta)

        await asyncio.gather(self.x.set(new_x_pos), self.y.set(new_y_pos))
