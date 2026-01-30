import asyncio
from math import radians

from ophyd_async.core import (
    SignalR,
    SignalRW,
    derived_signal_rw,
)
from ophyd_async.core._protocol import AsyncMovable
from ophyd_async.epics.motor import Motor

from dodal.devices.i05_shared.math import rotate_clockwise, rotate_counter_clockwise
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
            self.perp, self.long = create_rotational_ij_component_signals_with_motors(
                self.x, self.y, self.rotation_angle_deg
            )

    def _read_perp_calc(self, x: float, y: float, angle_deg: float) -> float:
        new_x, new_y = rotate_clockwise(radians(angle_deg), x, y)
        return new_x

    async def _set_perp_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = value
        long = self._read_long_calc(x_pos, y_pos, self.rotation_angle_deg)
        new_x, new_y = rotate_counter_clockwise(
            radians(self.rotation_angle_deg), perp, long
        )
        await asyncio.gather(self.x.set(new_x), self.y.set(new_y))

    def _read_long_calc(self, x: float, y: float, angle_deg: float) -> float:
        new_x, new_y = rotate_clockwise(radians(angle_deg), x, y)
        return new_y

    async def _set_long_calc(self, value: float) -> None:
        x_pos, y_pos = await asyncio.gather(
            self.x.user_readback.get_value(),
            self.y.user_readback.get_value(),
        )
        perp = self._read_perp_calc(x_pos, y_pos, self.rotation_angle_deg)
        long = value
        new_x, new_y = rotate_counter_clockwise(
            radians(self.rotation_angle_deg), perp, long
        )
        await asyncio.gather(self.x.set(new_x), self.y.set(new_y))


# NOTE: This already exists in ophyd-async but is not exposed publically in current
# release. It has been made public now https://github.com/bluesky/ophyd-async/pull/1172
# so the below can be removed once we move to latest ophyd-async release.
# @runtime_checkable
# class AsyncMovable(Protocol[T_co]):
#     @abstractmethod
#     def set(self, value: T_co) -> AsyncStatus:
#         """Return a ``Status`` that is marked done when the device is done moving."""


async def _get_angle_deg(angle_deg: SignalR[float] | float) -> float:
    if isinstance(angle_deg, SignalR):
        return await angle_deg.get_value()
    return angle_deg


def create_rotational_ij_component_signals(
    i_read: SignalR[float],
    j_read: SignalR[float],
    i_write: AsyncMovable[float],
    j_write: AsyncMovable[float],
    angle_deg: float | SignalR[float],
) -> tuple[SignalRW[float], SignalRW[float]]:
    """
    Create virtual "rotated" i and j component signals from two real motors.

    These virtual signals represent the i/j components after rotation by a given
    angle. When writing to these virtual signals, the real motor positions are
    adjusted using the inverse rotation so that the rotated component moves to the
    requested value.

    Args:
        i_read (SignalR): SignalR representing the i motor readback.
        j_read (SignalR): representing the j motor readback.
        i_write (AsyncReadable): object for setting the i position.
        j_write (AsyncReadbale): object for setting the j position.
        angle_deg (float | SignalR): Rotation angle in degrees.

    Returns:
        tuple[SignalRW[float], SignalRW[float]] Two virtual read/write signals
        corresponding to the rotated i and j components.
    """

    def _read_i_rotation_component_calc(i: float, j: float, angle_deg: float) -> float:
        new_i, new_j = rotate_clockwise(radians(angle_deg), i, j)
        return new_i

    async def _set_i_rotation_component_calc(value: float) -> None:
        """Move virtual i-axis to desired position while keeping j-axis constant in the
        rotated frame."""
        i_pos, j_pos, angle_deg_pos = await asyncio.gather(
            i_read.get_value(),
            j_read.get_value(),
            _get_angle_deg(angle_deg),
        )
        # Rotated coordinates
        i_rotation_target = value
        j_rotation_current = _read_j_rotation_component_calc(
            i_pos, j_pos, angle_deg_pos
        )
        # Convert back to motor frame by doing inverse rotation to determine actual motor positions
        new_i_pos, new_j_pos = rotate_counter_clockwise(
            radians(angle_deg_pos), i_rotation_target, j_rotation_current
        )
        await asyncio.gather(i_write.set(new_i_pos), j_write.set(new_j_pos))

    def _read_j_rotation_component_calc(i: float, j: float, angle_deg: float) -> float:
        new_i, new_j = rotate_clockwise(radians(angle_deg), i, j)
        return new_j

    async def _set_j_rotation_component_calc(value: float) -> None:
        """Move virtual j-axis to desired position while keeping j-axis constant in the
        rotated frame."""
        i_pos, j_pos, angle_deg_pos = await asyncio.gather(
            i_read.get_value(),
            j_read.get_value(),
            _get_angle_deg(angle_deg),
        )
        # Rotated coordinates
        i_rotation_target = _read_i_rotation_component_calc(i_pos, j_pos, angle_deg_pos)
        j_rotation_current = value
        # Convert back to motor frame by doing inverse rotation to determine actual motor positions
        new_i_pos, new_j_pos = rotate_counter_clockwise(
            radians(angle_deg_pos), i_rotation_target, j_rotation_current
        )
        await asyncio.gather(i_write.set(new_i_pos), j_write.set(new_j_pos))

    return derived_signal_rw(
        _read_i_rotation_component_calc,
        _set_i_rotation_component_calc,
        i=i_read,
        j=j_read,
        angle_deg=angle_deg,
    ), derived_signal_rw(
        _read_j_rotation_component_calc,
        _set_j_rotation_component_calc,
        i=i_read,
        j=j_read,
        angle_deg=angle_deg,
    )


def create_rotational_ij_component_signals_with_motors(
    i: Motor,
    j: Motor,
    angle_deg: float | SignalR[float],
) -> tuple[SignalRW[float], SignalRW[float]]:
    return create_rotational_ij_component_signals(
        i_read=i.user_readback,
        i_write=i,  # type: ignore
        j_read=j.user_readback,
        j_write=j,  # type: ignore
        angle_deg=angle_deg,
    )
