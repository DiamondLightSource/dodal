import pytest

from dodal.common import in_micros, step_to_num


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
