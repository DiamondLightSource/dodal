import asyncio
from math import radians

from bluesky.protocols import Movable
from bluesky.utils import maybe_await
from ophyd_async.core import (
    SignalR,
    SignalRW,
    derived_signal_rw,
)

from dodal.common.maths import rotate_clockwise, rotate_counter_clockwise


async def _get_angle_deg(angle_deg: SignalR[float] | float) -> float:
    if isinstance(angle_deg, SignalR):
        return await angle_deg.get_value()
    return angle_deg


def create_rotational_ij_component_signals(
    i_read: SignalR[float],
    j_read: SignalR[float],
    i_write: Movable[float],
    j_write: Movable[float],
    angle_deg: float | SignalR[float],
    clockwise_frame: bool = True,
) -> tuple[SignalRW[float], SignalRW[float]]:
    """Create virtual i/j signals representing a Cartesian coordinate frame
    that is rotated by a given angle relative to the underlying equipment axes.

    The returned signals expose the position of the system in a *rotated frame
    of reference* (e.g. the sample or stage frame), while transparently mapping
    reads and writes onto the real i/j signals in the fixed equipment (lab) frame.

    From the user's point of view, i and j behave like ordinary orthogonal
    Cartesian axes attached to the rotating object. Internally, all reads apply
    a rotation to the real motor positions, and all writes apply the inverse
    rotation so that the requested motion is achieved in the rotated frame.

    Args:
        i_read (SignalR): SignalR representing the i motor readback.
        j_read (SignalR): representing the j motor readback.
        i_write (Movable): object for setting the i position.
        j_write (Movable): object for setting the j position.
        angle_deg (float | SignalR): Rotation angle in degrees.
        clockwise_frame (boolean): If True, the rotated frame is defined using a
            clockwise rotation; otherwise, a counter-clockwise rotation is used.

    Returns:
        tuple[SignalRW[float], SignalRW[float]] Two virtual read/write signals
        corresponding to the rotated i and j components.
    """
    rotate = rotate_clockwise if clockwise_frame else rotate_counter_clockwise
    reverse_rotate = rotate_counter_clockwise if clockwise_frame else rotate_clockwise

    def _read_i_rotation_component_calc(i: float, j: float, angle_deg: float) -> float:
        new_i, new_j = rotate(radians(angle_deg), i, j)
        return new_i

    async def _set_i_rotation_component_calc(value: float) -> None:
        """Move virtual i-axis to desired position while keeping j-axis constant in the
        rotated frame.
        """
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
        new_i_pos, new_j_pos = reverse_rotate(
            radians(angle_deg_pos), i_rotation_target, j_rotation_current
        )
        await asyncio.gather(
            maybe_await(i_write.set(new_i_pos)), maybe_await(j_write.set(new_j_pos))
        )

    def _read_j_rotation_component_calc(i: float, j: float, angle_deg: float) -> float:
        new_i, new_j = rotate(radians(angle_deg), i, j)
        return new_j

    async def _set_j_rotation_component_calc(value: float) -> None:
        """Move virtual j-axis to desired position while keeping j-axis constant in the
        rotated frame.
        """
        i_pos, j_pos, angle_deg_pos = await asyncio.gather(
            i_read.get_value(),
            j_read.get_value(),
            _get_angle_deg(angle_deg),
        )
        # Rotated coordinates
        i_rotation_current = _read_i_rotation_component_calc(
            i_pos, j_pos, angle_deg_pos
        )
        j_rotation_target = value
        # Convert back to motor frame by doing inverse rotation to determine actual motor positions
        new_i_pos, new_j_pos = reverse_rotate(
            radians(angle_deg_pos), i_rotation_current, j_rotation_target
        )
        await asyncio.gather(
            maybe_await(i_write.set(new_i_pos)), maybe_await(j_write.set(new_j_pos))
        )

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
