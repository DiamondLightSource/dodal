import math
from collections.abc import Callable

import pydantic
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
    get_straight_line_y,
)

from .operator_inversion_pairing import OperatorInversionPairing


# expected success tests (the 'Happy Path'): All numbers here are arbitrary
@pytest.mark.parametrize("input,result", [(1.0, 0.1), (100.0, 10.0)])
def test_conversion_from_millimetres_to_centimetres(input, result):
    assert convert_mm_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 10), (0.1, 1.0)])
def test_conversion_from_centimetres_to_millimetres(input, result):
    assert convert_cm_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(0.01, 1.0), (1.0, 100.0)])
def test_conversion_to_percentage_from_factor(input, result):
    assert convert_factor_to_percentage(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 0.01), (100, 1.0)])
def test_conversion_to_factor_from_percentage(input, result):
    assert convert_percentage_to_factor(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1000.0, 1.0), (10000.0, 10.0)])
def test_conversion_from_microns_to_millimeters(input, result):
    assert convert_microns_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1.0, 1000.0), (10, 10000.0)])
def test_conversion_from_millimeters_to_microns(input, result):
    assert convert_mm_to_microns(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(1000, 1.0), (100, 0.1)])
def test_conversion_from_electronvolts_to_kiloelectronvolts(input, result):
    assert convert_ev_to_kev(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(10000.0, 1.0), (1000, 0.1)])
def test_conversion_from_microns_to_centimetres(input, result):
    assert convert_microns_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "c,m,x,expected_y",
    [
        (1.5, 1.0, 2.0, 3.5),
        (-1.5, 1.0, 10.0, 8.5),
        (3.5, -4.2, 7.2, -26.74),
        (-0.8, -0.14, -9.1, 0.474),
        (-2.4, 1.7, 2.8, 2.36),
        (0.0, 15.8, 0.0, 0.0),
        (0.0, -9.14, 0.0, 0.0),
        (0.0, 3.2, 11.6, 37.12),
        (0.0, -3.2, 11.6, -37.12),
        (0.0, 3.2, -11.6, -37.12),
        (0.1, -3.2, -11.6, 37.22),
        (5.2, 0.0, -8.64, 5.2),
    ],
)
def test_straight_line_conversion(c, m, x, expected_y):
    assert get_straight_line_y(line_offset=c, line_gradient=m, x=x) == pytest.approx(
        expected_y
    )


# Circular "sanity check" tests, exercise pairs of reciprocating functions
# proving the result of applying a function and its inverse results in the original value


@pytest.mark.parametrize(
    "f, g, numerical_args",
    [
        (
            convert_ev_to_kev,
            lambda k: k * 1000.0,
            [16.83, 0.0, 0.037, 1.0, 6.208, 18, 12345.6, 28906.4],
        ),
        (
            convert_mm_to_cm,
            convert_cm_to_mm,
            [-16.83, 0.0, 0.037, 1.0, 6.208, 18, 102.99],
        ),
        (
            convert_microns_to_cm,
            lambda x: convert_mm_to_microns(convert_cm_to_mm(x)),
            [-6.119, 0.0, 0.764, 1.02, 62.45, 12754, 3154.59],
        ),
        (
            convert_microns_to_mm,
            convert_mm_to_microns,
            [-12.38, 0.0, 0.307, 1.0, 6.45, 24, 231.089],
        ),
        (
            convert_factor_to_percentage,
            convert_percentage_to_factor,
            [0.0, 1.0, 0.5, 0.367, 27.404, 100.0, 99.8, 53.647],
        ),
    ],
)
def test_reciprocal_function_pairs_nest_consistent_with_identity(
    f: Callable[[float], float],
    g: Callable[[float], float],
    numerical_args: list[float],
):
    for op_pair in [
        OperatorInversionPairing(f, g),
        OperatorInversionPairing(g, f),
    ]:
        for x in numerical_args:
            assert op_pair.composed_operator_is_consistent_with_identity_operator(x)


# The inauspicuous path


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_microns_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_microns_to_cm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_ev_to_kev_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_ev_to_kev(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_microns_to_mm_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_microns_to_mm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_mm_to_microns_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_mm_to_microns(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), True],
)
def test_convert_factor_to_percentage_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_factor_to_percentage(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_percentage_to_factor_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_percentage_to_factor(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), False],
)
def test_convert_mm_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_mm_to_cm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), True],
)
def test_convert_cm_to_mm_raises_error_with_bad_input(bad_input):
    with pytest.raises(pydantic.ValidationError):
        convert_cm_to_mm(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.log, object(), False],
)
def test_straight_line_calculator_raises_error_with_bad_offset(bad_input):
    _probe_x = 11.1
    _line_gradient = -2.07
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(bad_input, _line_gradient, _probe_x)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.sin, object(), True],
)
def test_straight_line_calculator_raises_error_with_bad_gradient(bad_input):
    _probe_x = -11.1
    _line_offset = 14.2
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(_line_offset, bad_input, _probe_x)


@pytest.mark.parametrize(
    "bad_input",
    ["", "a", [], None, math.tan, object(), False],
)
def test_straight_line_calculator_raises_error_with_bad_x_value(bad_input):
    _line_offset = 0.1
    _line_gradient = 5.4
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(_line_offset, _line_gradient, bad_input)
