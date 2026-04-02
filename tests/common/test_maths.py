from math import pi

import numpy as np
import pytest

from dodal.common import in_micros, step_to_num
from dodal.common.maths import (
    AngleWithPhase,
    Rectangle2D,
    do_rotation,
    rotate_clockwise,
    rotate_counter_clockwise,
)


@pytest.mark.parametrize(
    "s,us",
    [
        (4.000_001, 4_000_001),
        (4.999_999, 4_999_999),
        (4, 4_000_000),
        (4.000_000_1, 4_000_001),
        (4.999_999_9, 5_000_000),
        (0.1, 100_000),
        (0.000_000_1, 1),
        (0, 0),
    ],
)
def test_in_micros(s: float, us: int):
    assert in_micros(s) == us


@pytest.mark.parametrize(
    "s", [-4.000_001, -4.999_999, -4, -4.000_000_5, -4.999_999_9, -4.05]
)
def test_in_micros_negative(s: float):
    with pytest.raises(ValueError):
        in_micros(s)


@pytest.mark.parametrize(
    "start,stop,step,expected_num,truncated_stop",
    [
        (0, 0, 1, 1, None),  # start=stop, 1 point at start
        (0, 0.5, 1, 1, 0),  # step>length, 1 point at start
        (0, 1, 1, 2, None),  # stop=start+step, point at start & stop
        (0, 0.99, 1, 2, 1),  # stop >= start + 0.99*step, included
        (0, 0.98, 1, 1, 0),  # stop < start + 0.99*step, not included
        (0, 1.01, 1, 2, 1),  # stop >= start + 0.99*step, included
        (0, 1.75, 0.25, 8, 1.75),
        (0, 0, -1, 1, None),  # start=stop, 1 point at start
        (0, 0.5, -1, 1, 0),  # abs(step)>length, 1 point at start
        (0, -1, 1, 2, None),  # stop=start+-abs(step), point at start & stop
        (0, -0.99, 1, 2, -1),  # stop >= start + 0.99*-abs(step), included
        (0, -0.98, 1, 1, 0),  # stop < start + 0.99*-abs(step), not included
        (0, -1.01, 1, 2, -1),  # stop >= start + 0.99*-abs(step), included
        (0, -1.75, 0.25, 8, -1.75),
        (1, 10, -0.901, 10, 9.109),  # length overrules step for direction
        (10, 1, -0.901, 10, 1.891),
    ],
)
def test_step_to_num(
    start: float,
    stop: float,
    step: float,
    expected_num: int,
    truncated_stop: float | None,
):
    truncated_stop = stop if truncated_stop is None else truncated_stop
    actual_start, actual_stop, num = step_to_num(start, stop, step)
    assert actual_start == start
    assert actual_stop == truncated_stop
    assert num == expected_num


@pytest.mark.parametrize(
    "x_1,y_1,x_2,y_2, inside, outside",
    [
        (0, 0, 10.0, 10.0, (5, 5), (15, 15)),
        (10, 10, 0.0, 0.0, (5, 5), (15, 15)),
        (-20, 0.0, 20, 10.0, (0, 5), (25, 15)),
        (-20, 10.0, 20, 0.0, (0, 5), (25, 15)),
    ],
)
def test_rectangle_contains(
    x_1: float,
    y_1: float,
    x_2: float,
    y_2: float,
    inside: tuple[float, float],
    outside: tuple[float, float],
):
    rect = Rectangle2D(x_1, y_1, x_2, y_2)
    assert rect.contains(*inside)
    assert not rect.contains(*outside)


@pytest.mark.parametrize(
    "x_1,y_1,x_2,y_2, max_x, max_y, min_x, min_y",
    [
        (0, 0, 10.0, 10.0, 10.0, 10.0, 0.0, 0.0),
        (-20, 0.0, 20, 10.0, 20.0, 10.0, -20.0, 0.0),
    ],
)
def test_rectangle_min_max(
    x_1: float,
    y_1: float,
    x_2: float,
    y_2: float,
    max_x: float,
    max_y: float,
    min_x: float,
    min_y: float,
):
    rect = Rectangle2D(x_1, y_1, x_2, y_2)
    assert rect.get_max_x() == max_x
    assert rect.get_max_y() == max_y
    assert rect.get_min_x() == min_x
    assert rect.get_min_y() == min_y


@pytest.mark.parametrize(
    "theta,x,y,expected",
    [
        (0.0, 1.0, 2.0, (1.0, 2.0)),
        (pi / 2, 1.0, 0.0, (0.0, -1.0)),  # 90 degress clockwise
        (pi, 1.0, 2.0, (-1.0, -2.0)),
        (2 * pi, 3.0, -4.0, (3.0, -4.0)),
    ],
)
def test_rotate_clockwise_known_angles(
    theta: float, x: float, y: float, expected: tuple[float, float]
) -> None:
    x_new, y_new = rotate_clockwise(theta, x, y)
    assert x_new == pytest.approx(expected[0])
    assert y_new == pytest.approx(expected[1])


@pytest.mark.parametrize(
    "theta,x,y,expected",
    [
        (0.0, 1.0, 2.0, (1.0, 2.0)),
        (pi / 2, 1.0, 0.0, (0.0, 1.0)),  # 90 degrees counter clockwise
        (pi, 1.0, 2.0, (-1.0, -2.0)),
    ],
)
def test_rotate_counter_clockwise_known_angles(
    theta: float, x: float, y: float, expected: tuple[float, float]
) -> None:
    x_new, y_new = rotate_counter_clockwise(theta, x, y)
    assert x_new == pytest.approx(expected[0])
    assert y_new == pytest.approx(expected[1])


def test_clockwise_and_counter_clockwise_are_inverses() -> None:
    x, y = 2.5, -1.3
    theta = 0.73

    x_rot, y_rot = rotate_clockwise(theta, x, y)
    x_back, y_back = rotate_counter_clockwise(theta, x_rot, y_rot)

    assert x_back == pytest.approx(x)
    assert y_back == pytest.approx(y)


def test_rotation_preserves_length():
    x, y = 3.0, 4.0
    theta = 1.234

    x_rot, y_rot = rotate_clockwise(theta, x, y)
    original = x**2 + y**2
    rotated = x_rot**2 + y_rot**2

    assert rotated == pytest.approx(original)


def test_do_rotation_matches_manual_matrix_multiply() -> None:
    x, y = 1.2, -0.4
    theta = 0.5
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    rotation_matrix = np.array(
        [
            [cos_theta, -sin_theta],
            [sin_theta, cos_theta],
        ]
    )
    x_new, y_new = do_rotation(x, y, rotation_matrix)
    expected = rotation_matrix @ np.array([x, y])

    assert x_new == pytest.approx(expected[0])
    assert y_new == pytest.approx(expected[1])


@pytest.mark.parametrize(
    "offset, phase, expected_offset, expected_phase",
    [
        [0, 0, 0, 0],
        [360, 0, 360, 0],
        [370, 0, 370, 0],
        [390, 30, 390, 30],
        [360, -30, 0, 330],
        [-270, -90, -630, 270],
    ],
)
def test_angle_with_phase_construct_from_offset_and_phase(
    offset: float, phase: float, expected_offset: float, expected_phase: float
):
    angle_with_phase = AngleWithPhase(offset, phase)
    assert angle_with_phase.offset == expected_offset
    assert angle_with_phase.phase == expected_phase


@pytest.mark.parametrize(
    "unwrapped, expected_offset, expected_phase",
    [
        [0, 0, 0],
        [270, 0, 270],
        [540, 360, 180],
        [-90, -360, 270],
        [180, 0, 180],
        [360, 360, 0],
    ],
)
def test_angle_with_phase_wrap(
    unwrapped: float, expected_offset: float, expected_phase: float
):
    angle_with_phase = AngleWithPhase.wrap(unwrapped)
    assert angle_with_phase.offset == expected_offset
    assert angle_with_phase.phase == expected_phase


@pytest.mark.parametrize(
    "offset, phase, expected_unwrapped",
    [
        [0, 0, 0],
        [360, 0, 360],
        [370, 0, 370],
        [390, 30, 420],
        [360, -30, 330],
        [-270, -90, -360],
    ],
)
def test_angle_with_phase_unwrap(
    offset: float, phase: float, expected_unwrapped: float
):
    angle_with_phase = AngleWithPhase(offset, phase)
    assert angle_with_phase.unwrap() == expected_unwrapped


@pytest.mark.parametrize(
    "offset1, phase1, offset2, phase2, expected_offset, expected_phase",
    [
        [0, 0, 360, 0, 0, 0],
        [0, 0, 10, 0, -350, 350],
        [0, 90, 370, 0, 10, 80],
    ],
)
def test_angle_with_phase_rebase(
    offset1: float,
    phase1: float,
    offset2: float,
    phase2: float,
    expected_offset: float,
    expected_phase: float,
):
    angle1 = AngleWithPhase(offset1, phase1)
    angle2 = AngleWithPhase(offset2, phase2)
    rebased = angle1.rebase_to(angle2)
    assert rebased.offset == expected_offset
    assert rebased.phase == expected_phase


@pytest.mark.parametrize(
    "offset1, phase1, offset2, phase2, expected_distance",
    [
        [0, 0, 360, 0, 0],
        [0, 0, 0, 330, 30],
        [0, 0, 0, 30, 30],
        [0, 1, 0, 359, 2],
        [0, 0, 0, 181, 179],
        [370, 0, 360, 0, 10],
    ],
)
def test_angle_with_phase_phase_distance(
    offset1: float,
    phase1: float,
    offset2: float,
    phase2: float,
    expected_distance: float,
):
    angle1 = AngleWithPhase(offset1, phase1)
    angle2 = AngleWithPhase(offset2, phase2)
    assert angle1.phase_distance(angle2) == expected_distance
    assert angle2.phase_distance(angle1) == expected_distance


@pytest.mark.parametrize(
    "offset, phase, target_phase, expected_offset, expected_phase",
    [
        [0, 0, 0, 0, 0],
        [0, 0, 270, -360, 270],
        [0, 0, 90, 0, 90],
        [360, 179, 181, 360, 181],
        [360, 181, 179, 360, 179],
        [360, 1, -1, 0, 359],
        [360, 1, 359, 0, 359],
    ],
)
def test_angle_with_phase_nearest_with_phase(
    offset: float,
    phase: float,
    target_phase: float,
    expected_offset: float,
    expected_phase: float,
):
    angle = AngleWithPhase(offset, phase)
    nearest = angle.nearest_with_phase(target_phase)
    assert nearest.offset == expected_offset
    assert nearest.phase == expected_phase


@pytest.mark.parametrize(
    "phase, expected_phase",
    [[1, 359], [-1, 1], [180, 180], [179, 181], [181, 179], [360, 0], [0, 0]],
)
def reflect_phase(phase: float, expected_phase: float):
    assert reflect_phase(phase) == expected_phase
