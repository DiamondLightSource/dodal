import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from math import radians

import pytest
from bluesky.protocols import Movable
from bluesky.utils import maybe_await
from ophyd_async.core import SignalR, SignalRW


@dataclass
class AxesTestConfig:
    i_read: SignalR[float]
    j_read: SignalR[float]
    i_write: Movable[float]
    j_write: Movable[float]
    angle_deg: float | Movable[float]
    expected_i_read_func: Callable[[float, float, float], float]
    expected_j_read_func: Callable[[float, float, float], float]
    i_rotation_axis: SignalRW[float]
    j_rotation_axis: SignalRW[float]


async def assert_set_axis_preserves_other(
    *,
    i_val: float,
    j_val: float,
    angle_deg_val: float,
    new_i_axis_value: float,
    new_j_axis_value: float,
    axes_config: AxesTestConfig,
) -> None:
    await asyncio.gather(
        maybe_await(axes_config.i_write.set(i_val)),
        maybe_await(axes_config.j_write.set(j_val)),
    )
    angle_deg = axes_config.angle_deg
    if isinstance(angle_deg, Movable):
        await maybe_await(angle_deg.set(angle_deg_val))

    theta = radians(angle_deg_val)

    # Capture invariant component before move
    expected_i = new_i_axis_value
    expected_j = axes_config.expected_j_read_func(i_val, j_val, theta)

    # Move axis to new position
    await axes_config.i_rotation_axis.set(expected_i)

    # Read back motors
    i_new, j_new = await asyncio.gather(
        axes_config.i_read.get_value(), axes_config.j_read.get_value()
    )

    # Compute rotated components after move
    i_val_after = axes_config.expected_i_read_func(i_new, j_new, theta)
    j_val_after = axes_config.expected_j_read_func(i_new, j_new, theta)

    assert i_val_after == pytest.approx(expected_i)
    assert j_val_after == pytest.approx(expected_j)

    await asyncio.gather(
        maybe_await(axes_config.i_write.set(i_val)),
        maybe_await(axes_config.j_write.set(j_val)),
    )
    angle_deg = axes_config.angle_deg
    if isinstance(angle_deg, Movable):
        await maybe_await(angle_deg.set(angle_deg_val))

    theta = radians(angle_deg_val)

    expected_j = new_j_axis_value
    expected_i = axes_config.expected_i_read_func(i_val, j_val, theta)

    # Move axis to new position
    await axes_config.j_rotation_axis.set(expected_j)

    # Read back motors
    i_new, j_new = await asyncio.gather(
        axes_config.i_read.get_value(), axes_config.j_read.get_value()
    )

    # Compute rotated components after move
    i_val_after = axes_config.expected_i_read_func(i_new, j_new, theta)
    j_val_after = axes_config.expected_j_read_func(i_new, j_new, theta)

    assert i_val_after == pytest.approx(expected_i)
    assert j_val_after == pytest.approx(expected_j)
