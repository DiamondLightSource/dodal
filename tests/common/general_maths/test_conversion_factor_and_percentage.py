import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_factor_to_percentage,
    convert_percentage_to_factor,
)

# expected success tests (the 'Happy Path'): All numbers here are arbitrary


@pytest.mark.parametrize("input,result", [(0.01, 1.0), (1.0, 100.0)])
def test_conversion_to_percentage_from_factor(input, result):
    assert convert_factor_to_percentage(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 0.01), (100, 1.0)])
def test_conversion_to_factor_from_percentage(input, result):
    assert convert_percentage_to_factor(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_factor_to_percentage_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_factor_to_percentage(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_percentage_to_factor_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_percentage_to_factor(bad_input)
