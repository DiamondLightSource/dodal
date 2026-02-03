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
    inverse_rotate = rotate_counter_clockwise if clockwise_frame else rotate_clockwise

    async def _read_rotated() -> tuple[float, float, float]:
        i, j, ang = await asyncio.gather(
            i_read.get_value(),
            j_read.get_value(),
            _get_angle_deg(angle_deg),
        )
        return (*rotate(radians(ang), i, j), ang)

    async def _write_rotated(i_rot: float, j_rot: float, ang: float) -> None:
        i_new, j_new = inverse_rotate(radians(ang), i_rot, j_rot)
        await asyncio.gather(
            maybe_await(i_write.set(i_new)),
            maybe_await(j_write.set(j_new)),
        )

    def _read_i(i: float, j: float, ang: float) -> float:
        return rotate(radians(ang), i, j)[0]

    async def _set_i(value: float) -> None:
        i_rot, j_rot, ang = await _read_rotated()
        await _write_rotated(value, j_rot, ang)

    def _read_j(i: float, j: float, ang: float) -> float:
        return rotate(radians(ang), i, j)[1]

    async def _set_j(value: float) -> None:
        i_rot, j_rot, ang = await _read_rotated()
        await _write_rotated(i_rot, value, ang)

    return (
        derived_signal_rw(_read_i, _set_i, i=i_read, j=j_read, ang=angle_deg),
        derived_signal_rw(_read_j, _set_j, i=i_read, j=j_read, ang=angle_deg),
    )
