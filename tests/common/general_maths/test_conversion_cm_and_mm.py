import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_cm_to_mm,
    convert_mm_to_cm,
)


# expected success tests (the 'Happy Path'): All numbers here are arbitrary
@pytest.mark.parametrize("input,result", [(1.0, 0.1), (100.0, 10.0)])
def test_conversion_from_millimetres_to_centimetres(input, result):
    assert convert_mm_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 10), (0.1, 1.0)])
def test_conversion_from_centimetres_to_millimetres(input, result):
    assert convert_cm_to_mm(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_mm_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_mm_to_cm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_cm_to_mm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_cm_to_mm(bad_input)
