import math

import pytest

from dodal.common.general_maths.check_bounds import is_within_range


@pytest.mark.parametrize(
    "lower_bound,upper_bound,tested_value,result",
    [
        (1, 3, 2, True),
        (-3, -1, -2, True),
        (-1, 1, 0, True),
        (-1, -0.1, -0.5, True),
        (0.1, 1, 0.5, True),
    ],
)
def test_is_within_range(
    lower_bound: float, upper_bound: float, tested_value: float, result: bool
):
    assert is_within_range(lower_bound, upper_bound, tested_value) == result


@pytest.mark.parametrize(
    "lower_bound,upper_bound,tested_value,result",
    [
        (1, 2, 3, False),
        (-3, -1, -4, False),
        (1, 2, 0, False),
        (-1, -0.1, -10.0, False),
        (0.1, 1, 1.5, False),
    ],
)
def test_is_outside_range(
    lower_bound: float, upper_bound: float, tested_value: float, result: bool
):
    assert is_within_range(lower_bound, upper_bound, tested_value) == result


def test_has_misordered_inputs():
    with pytest.raises(ValueError):
        is_within_range(4, -4, 1)


@pytest.mark.parametrize(
    "bad_input",
    [
        (
            "a",
            None,
            math.sin,
            object(),
        ),
    ],
)
def test_is_within_range_raises_error_with_bad_tested_value(
    bad_input,
):
    with pytest.raises(TypeError):
        is_within_range(-4, 4, bad_input)


@pytest.mark.parametrize(
    "bad_input",
    [
        (
            "a",
            None,
            math.sin,
            object(),
        ),
    ],
)
def test_is_within_range_raises_error_with_bad_upper_bound(
    bad_input,
):
    with pytest.raises(TypeError):
        is_within_range(-4, bad_input, 4)


@pytest.mark.parametrize(
    "bad_input",
    [
        (
            "a",
            None,
            math.sin,
            object(),
        ),
    ],
)
def test_is_within_range_raises_error_with_bad_lower_bound(
    bad_input,
):
    with pytest.raises(TypeError):
        is_within_range(bad_input, 4, 0)
