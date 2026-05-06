import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_microns_to_mm,
    convert_mm_to_microns,
)


# expected success tests (the 'Happy Path'): All numbers here are arbitrary
@pytest.mark.parametrize("input,result", [(1000.0, 1.0), (10000.0, 10.0)])
def test_conversion_from_microns_to_millimeters(input, result):
    assert convert_microns_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 1000.0), (10, 10000.0)])
def test_conversion_from_millimeters_to_microns(input, result):
    assert convert_mm_to_microns(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_microns_to_mm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_microns_to_mm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_mm_to_microns_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_mm_to_microns(bad_input)
