import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_cm_to_mm,
    convert_ev_to_kev,
    convert_factor_to_percentage,
    convert_microns_to_cm,
    convert_microns_to_mm,
    convert_mm_to_cm,
    convert_mm_to_microns,
    convert_percentage_to_factor,
)

# expected success tests (the 'Happy Path'):


@pytest.mark.parametrize("input,result", [(0.01, 1.0), (1.0, 100.0)])
def test_conversion_to_percentage_from_factor(input, result):
    assert convert_factor_to_percentage(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 0.01), (100, 1.0)])
def test_conversion_to_factor_from_percentage(input, result):
    assert convert_percentage_to_factor(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(10000.0, 1.0), (1000, 0.1)])
def test_conversion_from_microns_to_centimetres(input, result):
    assert convert_microns_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1000.0, 1.0), (10000.0, 10.0)])
def test_conversion_from_microns_to_millimeters(input, result):
    assert convert_microns_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 1000.0), (10, 10000.0)])
def test_conversion_from_millimeters_to_microns(input, result):
    assert convert_mm_to_microns(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 0.1), (100.0, 10.0)])
def test_conversion_from_millimetres_to_centimetres(input, result):
    assert convert_mm_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 10), (0.1, 1.0)])
def test_conversion_from_centimetres_to_millimetres(input, result):
    assert convert_cm_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1000, 1.0), (100, 0.1)])
def test_conversion_from_electronvolts_to_kiloelectronvolts(input, result):
    assert convert_ev_to_kev(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_cm_to_mm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_cm_to_mm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_ev_to_kev_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_ev_to_kev(bad_input)


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
def test_convert_microns_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_microns_to_cm(bad_input)


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
def test_convert_mm_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_mm_to_cm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_mm_to_microns_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_mm_to_microns(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_percentage_to_factor_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_percentage_to_factor(bad_input)
