import asyncio
from math import radians

from numpy import cos as c
from numpy import sin as s
from ophyd_async.core import SignalR, SignalRW, derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.i05_shared.math import CallableRotationMatrixType, rotate
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


ROTATION_MATRIX = (
    (c, s),
    (neg_s, c),
)


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
            # self.perp = derived_signal_rw(
            #     self._read_perp_calc,
            #     self._set_perp_calc,
            #     x=self.x,
            #     y=self.y,
            #     angle_deg=self.rotation_angle_deg,
            # )
            # self.long = derived_signal_rw(
            #     self._read_long_calc,
            #     self._set_long_calc,
            #     x=self.x,
            #     y=self.y,
            #     angle_deg=self.rotation_angle_deg,
            # )
            self.perp = create_rw_rotation_axis_signal(
                i=self.x,
                j=self.y,
                angle_deg=self.rotation_angle_deg,
                rotation_matrix=ROTATION_MATRIX,
                i_axis=True,
            )
            self.long = create_rw_rotation_axis_signal(
                i=self.x,
                j=self.y,
                angle_deg=self.rotation_angle_deg,
                rotation_matrix=ROTATION_MATRIX,
                i_axis=False,
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
        new_x, new_y = rotate(
            radians(self.rotation_angle_deg), perp, long, ROTATION_MATRIX, inverse=True
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
        new_x, new_y = rotate(
            radians(self.rotation_angle_deg), perp, long, ROTATION_MATRIX, inverse=True
        )
        await asyncio.gather(self.x.set(new_x), self.y.set(new_y))


def create_rw_rotation_axis_signal(
    i: Motor,
    j: Motor,
    angle_deg: SignalR[float] | float,
    rotation_matrix: CallableRotationMatrixType,
    i_axis: bool,
) -> SignalRW[float]:
    async def _get_angle_deg(angle_deg: SignalR[float] | float) -> float:
        if isinstance(angle_deg, SignalR):
            return await angle_deg.get_value()
        return angle_deg

    def _read_rotate_calc(
        i: float, j: float, angle_deg: float, return_i: bool
    ) -> float:
        new_i, new_j = rotate(radians(angle_deg), i, j, rotation_matrix)
        return new_i if return_i else new_j

    async def _set_inverse_rotate_calc(value: float) -> None:
        i_pos, j_pos, angle_deg_pos = await asyncio.gather(
            i.user_readback.get_value(),
            j.user_readback.get_value(),
            _get_angle_deg(angle_deg),
        )
        if i_axis:
            i_rotate = value
            j_rotate = _read_rotate_calc(i_pos, j_pos, angle_deg_pos, return_i=False)
        else:
            i_rotate = _read_rotate_calc(i_pos, j_pos, angle_deg_pos, return_i=True)
            j_rotate = value

        new_i, new_j = rotate(
            radians(angle_deg_pos), i_rotate, j_rotate, rotation_matrix, inverse=True
        )
        await asyncio.gather(i.set(new_i), j.set(new_j))

    return derived_signal_rw(
        _read_rotate_calc,
        _set_inverse_rotate_calc,
        i=i,
        j=j,
        angle_deg=angle_deg,
        return_i=i_axis,
    )
