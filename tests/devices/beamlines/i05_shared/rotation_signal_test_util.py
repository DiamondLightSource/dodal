import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from math import radians

import pytest
from bluesky.protocols import Movable
from bluesky.utils import maybe_await
from ophyd_async.core import SignalR, SignalRW


@dataclass
class RotatedCartesianFrameTestConfig:
    i_read: SignalR[float]
    j_read: SignalR[float]
    i_write: Movable[float]
    j_write: Movable[float]
    angle_deg: float | Movable[float]
    expected_i_read_func: Callable[[float, float, float], float]
    expected_j_read_func: Callable[[float, float, float], float]
    i_rotation_axis: SignalRW[float]
    j_rotation_axis: SignalRW[float]


async def _set_initial_state(
    i_val: float,
    j_val: float,
    angle_deg_val: float,
    frame_config: RotatedCartesianFrameTestConfig,
) -> None:
    await asyncio.gather(
        maybe_await(frame_config.i_write.set(i_val)),
        maybe_await(frame_config.j_write.set(j_val)),
    )
    if isinstance(frame_config.angle_deg, Movable):
        await maybe_await(frame_config.angle_deg.set(angle_deg_val))


async def _read_rotated_components(
    frame_config: RotatedCartesianFrameTestConfig, theta: float
) -> tuple[float, float]:
    i_new, j_new = await asyncio.gather(
        frame_config.i_read.get_value(),
        frame_config.j_read.get_value(),
    )
    return (
        frame_config.expected_i_read_func(i_new, j_new, theta),
        frame_config.expected_j_read_func(i_new, j_new, theta),
    )


async def _assert_setting_axis_preserves_other(
    set_axis: SignalRW[float],
    set_value: float,
    expected_i: float,
    expected_j: float,
    frame_config: RotatedCartesianFrameTestConfig,
    theta: float,
) -> None:
    await set_axis.set(set_value)
    i_after, j_after = await _read_rotated_components(
        frame_config=frame_config, theta=theta
    )
    assert i_after == pytest.approx(expected_i)
    assert j_after == pytest.approx(expected_j)


async def assert_rotated_axes_are_orthogonal(
    i_val: float,
    j_val: float,
    angle_deg_val: float,
    new_i_axis_value: float,
    new_j_axis_value: float,
    frame_config: RotatedCartesianFrameTestConfig,
) -> None:
    """Assert that the virtual rotated axes behave as independent Cartesian
    coordinates.

    This helper verifies that setting one virtual axis in a rotated frame
    updates only that axis while preserving the orthogonal axis in the same
    rotated frame.

    Specifically, the test:
    - Initializes the underlying i/j motors and rotation angle.
    - Sets the virtual i' axis and asserts that:
        * i' moves to the requested value
        * j' remains unchanged
    - Resets the system.
    - Sets the virtual j' axis and asserts that:
        * j' moves to the requested value
        * i' remains unchanged

    This confirms that the virtual axes form a proper orthogonal Cartesian
    coordinate frame, and that inverse rotations are applied correctly when
    writing to the underlying motors.

    Args:
        i_val: Initial value for the underlying i-axis.
        j_val: Initial value for the underlying j-axis.
        angle_deg_val: Rotation angle (in degrees) defining the rotated frame.
        new_i_axis_value: Target value for the virtual i' axis.
        new_j_axis_value: Target value for the virtual j' axis.
        frame_config: Configuration describing how virtual rotated axes are derived from
            the underlying motors, including expected readout functions.
    """
    # Test setting i′ preserves j′
    await _set_initial_state(
        i_val=i_val,
        j_val=j_val,
        angle_deg_val=angle_deg_val,
        frame_config=frame_config,
    )
    theta = radians(angle_deg_val)
    expected_j = frame_config.expected_j_read_func(i_val, j_val, theta)

    await _assert_setting_axis_preserves_other(
        set_axis=frame_config.i_rotation_axis,
        set_value=new_i_axis_value,
        expected_i=new_i_axis_value,
        expected_j=expected_j,
        frame_config=frame_config,
        theta=theta,
    )
    # Test setting j′ preserves i′
    await _set_initial_state(
        i_val=i_val,
        j_val=j_val,
        angle_deg_val=angle_deg_val,
        frame_config=frame_config,
    )
    expected_i = frame_config.expected_i_read_func(i_val, j_val, theta)
    await _assert_setting_axis_preserves_other(
        set_axis=frame_config.j_rotation_axis,
        set_value=new_j_axis_value,
        expected_i=expected_i,
        expected_j=new_j_axis_value,
        frame_config=frame_config,
        theta=theta,
    )
