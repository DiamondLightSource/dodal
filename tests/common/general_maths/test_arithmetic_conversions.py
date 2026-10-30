import math
from collections.abc import Callable
from typing import Any, Final

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
    parametric_fraction,
    parametrised_value,
)
from dodal.common.general_maths.interval import DirectedSegment, FloatInterval
from tests.common.general_maths.operator_inversion_pairing import (
    OperatorInversionPairing,
)
from tests.common.general_maths.test_interval import ALL_CONCRETE_INTERVAL_TYPES


# expected success tests (the 'Happy Path'): All numbers here are arbitrary
@pytest.mark.parametrize(
    "input,result", [(19.2, 1.92), (105.1, 10.51), (0, 0), (0.72, 0.072)]
)
def test_conversion_from_millimetres_to_centimetres(input, result) -> None:
    assert convert_mm_to_cm(input) == pytest.approx(result)


@pytest.mark.parametrize("input,result", [(3.6, 36), (2, 20), (0, 0), (0.254, 2.54)])
def test_conversion_from_centimetres_to_millimetres(input, result) -> None:
    assert convert_cm_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result", [(0.063, 6.3), (1, 100), (0, 0), (0.548, 54.8)]
)
def test_conversion_to_percentage_from_factor(input, result) -> None:
    assert convert_factor_to_percentage(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result", [(1.0, 0.01), (100, 1), (0, 0), (82.6, 0.826), (0.4, 0.004)]
)
def test_conversion_to_factor_from_percentage(input, result) -> None:
    assert convert_percentage_to_factor(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result", [(0, 0), (512.4, 0.5124), (1000.0, 1.0), (12708.0, 12.708)]
)
def test_conversion_from_microns_to_millimeters(input, result) -> None:
    assert convert_microns_to_mm(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result", [(0, 0), (0.42, 420), (1.0, 1000.0), (12.5, 12500.0)]
)
def test_conversion_from_millimeters_to_microns(input, result) -> None:
    assert convert_mm_to_microns(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result", [(12398.425, 12.398425), (2050, 2.05), (813, 0.813)]
)
def test_conversion_from_electronvolts_to_kiloelectronvolts(input, result) -> None:
    assert convert_ev_to_kev(input) == pytest.approx(result)


@pytest.mark.parametrize(
    "input,result",
    [(0, 0), (40000.0, 4.0), (1200, 0.12), (7056, 0.7056), (804.2, 0.08042)],
)
def test_conversion_from_microns_to_centimetres(input, result) -> None:
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
def test_straight_line_conversion(c, m, x, expected_y) -> None:
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
) -> None:
    for op_pair in [
        OperatorInversionPairing(f, g),
        OperatorInversionPairing(g, f),
    ]:
        for x in numerical_args:
            assert op_pair.composed_operator_is_consistent_with_identity_operator(x)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "interpolation_fraction, start, end, expected_result",
    [
        (0.1, 10, 20, 11),
        (0.2, 20, 10, 18),
        (0.1, 20.0, 10.0, 19.0),
        (0.5, -8.4, 8.4, 0),
        (0.75, -20, 60, 40),
        (0.9, 10, 91, 82.9),
        (0.3, 8.4, -8.4, 3.36),
        (0.2, -200.0, -100.0, -180.0),
        (0.5, 8.1, -8.1, 0),
    ],
)
def test_all_interval_types_strictly_interpolate_correctly(
    interval_cls: type[FloatInterval],
    interpolation_fraction: float,
    start: float,
    end: float,
    expected_result: float,
) -> None:
    segment = DirectedSegment.create(
        start=start,
        end=end,
        interval_cls=interval_cls
    )
    assert parametrised_value(
        normalising_directed_segment=segment,
        parametric_fraction=interpolation_fraction,
    ) == pytest.approx(expected_result)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end, expected_results",
    [
        (10, 20, [-38, -10, 10, 12.5, 20, 35, 78, 1020]),
        (-8.4, 8.4, [-89.04, -42, -8.4, -4.2, 8.4, 33.6, 105.84, 1688.4]),
        (-20, 60, [-404, -180, -20, 0, 60, 180, 524, 8060]),
        (10, 91, [-378.8, -152, 10, 30.25, 91, 212.5, 560.8, 8191]),
        (-200.0, -100.0, [-680, -400, -200, -175, -100, 50, 480, 9900]),
    ],
)
def test_all_interval_types_parametrically_convert_correctly(
    interval_cls: type[FloatInterval],
    start: float,
    end: float,
    expected_results: list[float],
) -> None:
    interpolation_fractions = (-4.8, -2, 0, 0.25, 1, 2.5, 6.8, 101)
    segment = DirectedSegment.create(
        start=start,
        end=end,
        interval_cls=interval_cls
    )
    for expected, fraction in zip(
        expected_results, interpolation_fractions, strict=True
    ):
        assert parametrised_value(
            normalising_directed_segment=segment,
            parametric_fraction=fraction,
            strictly_interpolation=False,
        ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value, expected_interval_fraction",
    [
        (
            -50,
            0,
        ),
        (
            50,
            1,
        ),
        (
            0,
            0.5,
        ),
        (
            40,
            0.9,
        ),
        (
            65.8,
            1.158,
        ),
        (-72.5, -0.225),
        (500, 5.5),
        (-500, -4.5),
    ],
)
@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
def test_that_reverse_parametrising_value_relative_to_interval_produces_correct_parametric_fraction(
    value: float, expected_interval_fraction: float, interval_cls: type[FloatInterval]
) -> None:
    segment = DirectedSegment.create(start=-50, end=50, interval_cls=interval_cls)
    f = parametric_fraction(normalising_directed_segment=segment, value=value)
    assert f == pytest.approx(expected_interval_fraction)


# The inauspicuous path

NON_NUMERICAL_EXAMPLES: Final[list[Any]] = [
    "",
    "a",
    [],
    None,
    math.sin,
    object(),
    KeyError(),
    False,
    True,
]


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_microns_to_cm_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_microns_to_cm(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_ev_to_kev_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_ev_to_kev(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_microns_to_mm_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_microns_to_mm(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_mm_to_microns_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_mm_to_microns(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_factor_to_percentage_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_factor_to_percentage(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_percentage_to_factor_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_percentage_to_factor(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_mm_to_cm_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_mm_to_cm(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_convert_cm_to_mm_raises_error_with_non_numerical_input(
    non_numerical_input,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        convert_cm_to_mm(non_numerical_input)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_straight_line_calculator_raises_error_with_bad_offset(
    non_numerical_input,
) -> None:
    _probe_x = 11.1
    _line_gradient = -2.07
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(non_numerical_input, _line_gradient, _probe_x)


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_straight_line_calculator_raises_error_with_bad_gradient(
    non_numerical_input,
) -> None:
    _probe_x = -11.1
    _line_offset = 14.2
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(_line_offset, non_numerical_input, _probe_x)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize("extraneous", [-48.9, -6, -0.001, 1.02, 58, 9012.723])
@pytest.mark.parametrize("start,end", [
    (-3.82, 59.52,),
    ( -3, -4),
    (99, 77,),
    (-200.9423, -11.4,),
    (-11.4, -256.12,),
])
def test_that_all_interval_types_refuse_to_extrapolate_when_strictly_interpolating(
    interval_cls: type[FloatInterval], extraneous: float, start: float, end: float,
) -> None:
    segment = DirectedSegment.create(
        start=start,
        end=end,
        interval_cls=interval_cls
    )
    with pytest.raises(ValueError):
        parametrised_value(
            normalising_directed_segment=segment,
            parametric_fraction=extraneous
        )


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
@pytest.mark.parametrize(
    "strictly_interpolation",
    (
        True,
        False,
    ),
)
@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start,end",
    [
        (-3.82, 59.52,),
        ( -3, -4),
        (99, 77,),
        (-200.9423, -11.4,),
        (-11.4, -256.12,),
    ]
)
def test_that_error_raised_when_parametrising_interval_with_non_numerical_fraction(
    non_numerical_input: Any,
    strictly_interpolation: bool,
    interval_cls: type[FloatInterval],
    start: float,
    end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    with pytest.raises(ValueError):
        parametrised_value(
            normalising_directed_segment=segment,
            parametric_fraction=non_numerical_input,
            strictly_interpolation=strictly_interpolation,
        )


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start,end",
    [
        (-3.82, 59.52,),
        ( -3, -4),
        (99, 77,),
        (-200.9423, -11.4,),
        (-11.4, -256.12,),
    ]
)
def test_that_error_raised_when_reverse_parametrising_non_numerical_value_relative_to_interval(
    non_numerical_input: Any,
    interval_cls: type[FloatInterval],
    start: float,
    end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    with pytest.raises(ValueError):
        parametric_fraction(
            normalising_directed_segment=segment,
            value=non_numerical_input
        )


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "strictly_interpolation",
    (
        True,
        False,
    ),
)
def test_that_error_raised_when_parametrising_intervals_instead_of_segments(
    interval_cls: type[FloatInterval],
    strictly_interpolation: bool,
) -> None:
    interval_rather_than_required_segment: Any = interval_cls(
        lower=-45.2,
        upper=23.6
    )
    with pytest.raises(ValueError):
        parametrised_value(
            normalising_directed_segment=interval_rather_than_required_segment,
            parametric_fraction=0.435,
            strictly_interpolation=strictly_interpolation,
        )

@pytest.mark.parametrize(
    "non_segment_input",
    NON_NUMERICAL_EXAMPLES
)
@pytest.mark.parametrize(
    "strictly_interpolation",
    (
        True,
        False,
    ),
)
def test_that_error_raised_when_parametrising_non_valid_segment(
    non_segment_input: Any,
    strictly_interpolation: bool,
) -> None:
    with pytest.raises(ValueError):
        parametrised_value(
            normalising_directed_segment=non_segment_input,
            parametric_fraction=0.435,
            strictly_interpolation=strictly_interpolation,
        )


@pytest.mark.parametrize(
    "non_numerical_input",
    NON_NUMERICAL_EXAMPLES,
)
def test_straight_line_calculator_raises_error_with_bad_x_value(
    non_numerical_input,
) -> None:
    _line_offset = 0.1
    _line_gradient = 5.4
    with pytest.raises(pydantic.ValidationError):
        get_straight_line_y(_line_offset, _line_gradient, non_numerical_input)
