import math
import sys
from typing import Any, Final

import pytest

from dodal.common.general_maths.interval import (
    ClosedInterval,
    DirectedSegment,
    HomogeneouslyTerminatedInterval,
    OpenInterval,
    _ForwardSegment,
    _InvertedSegment,
    _is_finite_real,
)

INTERVAL_TYPES: tuple[type[ClosedInterval] | type[OpenInterval], ...] = (
    ClosedInterval,
    OpenInterval,
)


# Happy path

REALS: Final[tuple[float, ...]] = (
    0,
    -1,
    -4,
    -77.109,
    -0.00013,
    -1.0e12,
    0.0,
    5,
    6089,
    70.14,
    6.7e11,
)


@pytest.mark.parametrize("r", REALS)
def test_that_finite_realness_check_recognises_real_finite_numbers(r: float) -> None:
    assert _is_finite_real(r)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "probed_x, lower, upper",
    [
        (
            0.0,
            -1.5,
            2.1,
        ),
        (
            4.2,
            1.2,
            402.87,
        ),
        (
            -7.09,
            -14.2,
            -5.44,
        ),
    ],
)
def test_that_intervals_recognise_enclosed_point(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    probed_x: float,
    lower: float,
    upper: float,
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert probed_x in interval


@pytest.mark.parametrize(
    "_lower, _upper",
    [
        (-1, 1),
        (0, 1),
        (6, 8),
        (-3, 0),
        (-12, -10),
    ],
)
# using int here to reduce test brittleness
def test_that_closed_interval_includes_its_endpoints(_lower: int, _upper: int):
    closed_interval = ClosedInterval(lower=_lower, upper=_upper)

    for bound in (_lower, _upper):
        assert bound in closed_interval


@pytest.mark.parametrize(
    "_lower, _upper",
    [
        (-1, 1),
        (0, 1),
        (6, 8),
        (-3, 0),
        (-12, -10),
    ],
)
# using int here to reduce test brittleness
def test_that_open_interval_excludes_its_endpoints(_lower: int, _upper: int):
    open_interval = OpenInterval(lower=_lower, upper=_upper)

    for bound in (_lower, _upper):
        assert bound not in open_interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (4, 7),
        (-5, 8),
        (8, 3),
        (-1, -100),
        (2.3, 4.5),
        (6.2, -7.89),
        (10, -3.51),
        (-41.2, -140.83),
    ],
)
def test_that_directed_segment_can_be_created_using_either_type_of_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(
        start=start,
        end=end,
        interval_cls=interval_cls,
    )
    assert isinstance(segment, DirectedSegment)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "expected_span, lower, upper",
    [
        (
            15.6,
            1.2,
            16.8,
        ),
        (
            15.6,
            -16.8,
            -1.2,
        ),
        (
            6.8,
            -2.1,
            4.7,
        ),
        (
            4.08,
            0,
            4.08,
        ),
        (
            33,
            12,
            45,
        ),
    ],
)
def test_that_all_interval_types_report_correct_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    expected_span: float,
    lower: float,
    upper: float,
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert interval.span == pytest.approx(expected_span)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "expected_span, start, end",
    [
        (
            -10,
            1,
            -9,
        ),
        (
            15.6,
            -16.8,
            -1.2,
        ),
        (
            6.8,
            -2.1,
            4.7,
        ),
        (
            -4.08,
            5.18,
            1.1,
        ),
        (
            33,
            12,
            45,
        ),
    ],
)
def test_that_directed_segments_report_correct_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    expected_span: float,
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment.span == pytest.approx(expected_span)


@pytest.mark.parametrize("interval_cls", INTERVAL_TYPES)
@pytest.mark.parametrize(
    "probed_x, lower, upper",
    [
        (
            10.0,
            -1.5,
            2.1,
        ),
        (
            -4.2,
            1.2,
            402.87,
        ),
        (
            -17.09,
            -14.2,
            -5.44,
        ),
    ],
)
def test_that_interval_does_not_contain_unambiguously_external_point(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    probed_x: float,
    lower: float,
    upper: float,
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert probed_x not in interval


@pytest.mark.parametrize("interval_cls", INTERVAL_TYPES)
@pytest.mark.parametrize(
    "probed_x, start, end",
    [
        (
            -10.0,
            1.5,
            -2.1,
        ),
        (
            -4.2,
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
            -5.44,
        ),
    ],
)
def test_that_segment_does_not_contain_unambiguously_external_point(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    probed_x: float,
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert probed_x not in segment


@pytest.mark.parametrize("interval_cls", INTERVAL_TYPES)
@pytest.mark.parametrize(
    "probed_x, start, end",
    [
        (
            0.1,
            1.5,
            -2.1,
        ),
        (
            67.2,
            1.2,
            402.87,
        ),
        (
            11.09,
            14.2,
            -5.44,
        ),
    ],
)
def test_that_segments_recognise_enclosed_point(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    probed_x: float,
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert probed_x in segment


@pytest.mark.parametrize("interval_cls", INTERVAL_TYPES)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_interval_recognises_another_interval_straddling_originals_endpoint_is_not_enclosed(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    parametrised_interval = interval_cls(lower=lower, upper=upper)
    tenth = 0.1 * parametrised_interval.span
    straddling = interval_cls(lower=lower + tenth, upper=upper + 2 * tenth)
    assert straddling not in parametrised_interval


@pytest.mark.parametrize("interval_cls", INTERVAL_TYPES)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_interval_does_not_contain_disjoint_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    disjoint_interval = ClosedInterval(lower=801.4, upper=952.93)
    parametrised_interval = interval_cls(lower=lower, upper=upper)
    assert disjoint_interval not in parametrised_interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_interval_contains_an_enclosed_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    enclosed_interval = ClosedInterval(lower=1.4, upper=1.93)
    parameterised_enclosure = interval_cls(lower=lower, upper=upper)
    assert enclosed_interval in parameterised_enclosure


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_any_interval_contains_itself(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    parameterised_interval = interval_cls(lower=lower, upper=upper)
    assert parameterised_interval in parameterised_interval


@pytest.mark.parametrize(
    "outer_cls, inner_cls, as_expected_by_types",
    [
        (ClosedInterval, ClosedInterval, True),
        (ClosedInterval, OpenInterval, True),
        (OpenInterval, ClosedInterval, False),
        (OpenInterval, OpenInterval, True),
    ],
)
def test_that_interval_containment_at_shared_lower_boundary_meets_expectations(
    outer_cls: type[ClosedInterval] | type[OpenInterval],
    inner_cls: type[ClosedInterval] | type[OpenInterval],
    as_expected_by_types: bool,
) -> None:
    wider = outer_cls(lower=0.0, upper=10.0)
    narrower = inner_cls(lower=0.0, upper=5.0)

    assert (narrower in wider) is as_expected_by_types


@pytest.mark.parametrize(
    "outer_cls, inner_cls, as_expected_by_types",
    [
        (ClosedInterval, ClosedInterval, True),
        (ClosedInterval, OpenInterval, True),
        (OpenInterval, ClosedInterval, False),
        (OpenInterval, OpenInterval, True),
    ],
)
def test_that_interval_containment_at_shared_upper_boundary_meets_expectations(
    outer_cls: type[ClosedInterval] | type[OpenInterval],
    inner_cls: type[ClosedInterval] | type[OpenInterval],
    as_expected_by_types: bool,
) -> None:
    wider = outer_cls(lower=0.0, upper=10.0)
    narrower = inner_cls(lower=2.0, upper=10.0)

    assert (narrower in wider) is as_expected_by_types


@pytest.mark.parametrize(
    "outer_cls, inner_cls, as_expected_by_types",
    [
        (ClosedInterval, ClosedInterval, True),
        (ClosedInterval, OpenInterval, True),
        (OpenInterval, ClosedInterval, False),
        (OpenInterval, OpenInterval, True),
    ],
)
def test_that_interval_containment_meets_expectations_when_all_endpoints_are_common(
    outer_cls: type[ClosedInterval] | type[OpenInterval],
    inner_cls: type[ClosedInterval] | type[OpenInterval],
    as_expected_by_types: bool,
) -> None:
    an_interval = outer_cls(lower=0.0, upper=10.0)
    coterminous = inner_cls(lower=0.0, upper=10.0)

    assert (coterminous in an_interval) is as_expected_by_types


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_interval_lower_end_points_are_not_modifiable(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    initial_span = interval.span
    with pytest.raises(ValueError):
        # modification attempt fails
        interval.lower = lower - 5.1
    # verify end points remained
    assert interval.span == pytest.approx(initial_span) and interval.lower == lower


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_interval_upper_end_points_are_not_modifiable(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    initial_span = interval.span
    with pytest.raises(ValueError):
        # modification attempt fails
        interval.upper = lower + 2.78 * initial_span
    # verify end points remained
    assert interval.span == pytest.approx(initial_span) and interval.upper == upper


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_segment_start_points_are_not_modifiable(
    interval_cls: type[ClosedInterval] | type[OpenInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    initial_span = segment.span
    with pytest.raises(ValueError):
        # modification attempt fails
        segment.start = start + 1.38 * initial_span
    # verify end points remained
    assert segment.span == pytest.approx(initial_span) and segment.start == start


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (
            -1.5,
            2.1,
        ),
        (
            1.2,
            402.87,
        ),
        (
            -17.09,
            14.2,
        ),
    ],
)
def test_that_segment_end_points_are_not_modifiable(
    interval_cls: type[ClosedInterval] | type[OpenInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    initial_span = segment.span
    with pytest.raises(ValueError):
        # modification attempt fails
        segment.end = start - 5.91 * initial_span
    # verify end points remained
    assert segment.span == pytest.approx(initial_span) and segment.end == end


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "a, b",
    [
        (11.5, -2.1),
        (617.2, 1.2),
        (91.329, -15.44),
        (14.39, -15),
        (2, 16.083),
        (0, 1),
        (1, 0),
        (-4, -81),
        (17, 95),
        (-8.15239, 0),
        (0.001, -0.004),
    ],
)
def test_that_interval_is_equal_to_itself(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    a: float,
    b: float,
) -> None:
    interval = interval_cls(lower=min(a, b), upper=max(a, b))
    assert interval == interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (11.5, -2.1),
        (617.2, 1.2),
        (91.329, -15.44),
        (14.39, -15),
        (2, 16.083),
        (0, 1),
        (1, 0),
        (-4, -81),
        (17, 95),
        (-8.15239, 0),
        (0.001, -0.004),
    ],
)
def test_that_segment_is_equal_to_itself(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment == segment


OTHER_TYPES: Final[tuple[Any, ...]] = (
    "",
    "Hello",
    "3.5",
    "-16",
    4.2,
    -12,
    0,
    19,
    -510.82,
    KeyError(),
    math.sin,
    True,
    False,
    object(),
    "&",
)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "other",
    OTHER_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (11.5, -2.1),
        (617.2, 1.2),
        (91.329, -15.44),
    ],
)
def test_that_segment_is_not_equal_to_other_types(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    other: Any,
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment != other


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (11.5, -2.1),
        (617.2, 1.2),
        (91.329, -15.44),
        (14.39, -15),
        (2, 16.083),
        (0, 1),
        (1, 0),
        (-4, -81),
        (17, 95),
        (-8.15239, 0),
        (0.001, -0.004),
    ],
)
def test_that_segment_is_not_equal_to_its_own_internal_backing_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment != segment._interval


@pytest.mark.parametrize(
    "interval_cls1",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "interval_cls2",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (1.5, -2.1),
        (67.2, 1.2),
        (19.379, -15.44),
    ],
)
def test_that_segment_equality_depends_on_interval_equality(
    interval_cls1: type[ClosedInterval] | type[OpenInterval],
    interval_cls2: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment1 = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls1)
    segment2 = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls2)
    assert bool(segment1 == segment2) == bool(interval_cls1 == interval_cls2)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (0, 1),
        (2, 1),
        (-5, -44),
        (44, -9),
        (-127, 11),
        (-5, 0),
        (5, 0),
        (0, -35),
        (16.5, 85.4),
        (-67.2, 115.2),
        (18.301, -92.44),
        (1.05, -2.1),
        (67.2, 1.2),
        (19.379, -15.44),
    ],
)
def test_that_inverted_segment_has_opposite_orientation(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    inverted = ~segment

    assert inverted.start == segment.end
    assert inverted.end == segment.start


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (0, 1),
        (2, 1),
        (-5, -44),
        (44, -9),
        (-127, 11),
        (-5, 0),
        (5, 0),
        (0, -35),
        (16.5, 85.4),
        (-67.2, 115.2),
        (18.301, -92.44),
        (1.05, -2.1),
        (67.2, 1.2),
        (19.379, -15.44),
    ],
)
def test_that_doubly_inverted_segment_equals_the_original(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    doubly_inverted = ~(~segment)

    assert doubly_inverted == segment


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (0, 10),
        (12, 4),
        (-2, -41),
        (85, -169),
        (-17, 101),
        (-6, 0),
        (8, 0),
        (0, -3),
        (1.55, 25.4),
        (-63.2, 105.02),
        (38.391, -129.404),
        (1.25, -2.61),
        (47.2, 7.2),
        (19.319, -315.94),
    ],
)
def test_that_inverted_segment_has_negated_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    inverted = ~segment
    assert inverted.span == -(segment.span)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (1.5, -2.1),
        (67.2, 1.2),
        (11.09, 14.2),
        (12.309, -5.44),
        (7.5, -12.1),
        (17.2, 9.2),
        (1.045, 28.2),
        (19.379, -15.44),
    ],
)
def test_that_segment_is_not_equal_to_its_own_inverse(
    interval_cls: type[ClosedInterval] | type[OpenInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    swapped = ~segment
    assert segment != swapped


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "c, d",
    [
        (1.5, -2.1),
        (67.2, 1.2),
        (11.09, 14.2),
        (12.309, -5.44),
        (7.5, -12.1),
        (17.2, 9.2),
        (1.045, 28.2),
        (19.379, -15.44),
    ],
)
def test_that_segment_is_not_equal_to_another_with_distinct_ends(
    interval_cls: type[ClosedInterval] | type[OpenInterval], c: float, d: float
) -> None:
    a = 5.1
    b = 23.458
    segment1 = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    segment2 = DirectedSegment.create(start=a + c, end=b + d, interval_cls=interval_cls)
    assert segment1 != segment2


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "a, b, x, expected_fraction",
    [
        (1.5, -2.1, 0.1, 0.38888889),
        (1.5, -2.1, -0.1, 0.44444444),
        (9, 17, 15, 0.75),
        (12.2, 1.8, 15, -0.26923076923),
        (100, 200, 123, 0.23),
        (100, 0, 48, 0.52),
    ],
)
def test_that_inverse_linear_interpolation_against_directed_segment_gives_expected_fraction(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    a: float,
    b: float,
    x: float,
    expected_fraction: float,
) -> None:
    segment = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    fraction = segment.inverse_linear_interpolated_value(value=x)
    assert fraction == pytest.approx(expected_fraction)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "a, b, expected_value, fraction",
    [
        (1.5, -2.1, 0.1, 0.38888889),
        (1.5, -2.1, -0.1, 0.44444444),
        (9, 17, 15, 0.75),
        (12.2, 1.8, 15, -0.26923076923),
        (100, 200, 123, 0.23),
        (100, 0, 48, 0.52),
    ],
)
def test_that_directed_segment_linear_interpolation_converts_parametric_fraction_to_expected_value(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    a: float,
    b: float,
    expected_value: float,
    fraction: float,
) -> None:
    segment = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    interpolated_value = segment.linear_interpolation_of_fraction(
        fractional_parameter=fraction
    )
    assert interpolated_value == pytest.approx(expected_value)


# Inauspicious path

NON_REALS: Final[tuple[Any, ...]] = (
    "",
    "Hello",
    "3.5",
    "-16",
    KeyError(),
    math.sin,
    True,
    False,
    object(),
    "&",
    complex(real=-1, imag=6.3),
    complex(real=12.083, imag=14),
)

NON_FINITE_FLOATS: Final[tuple[float, ...]] = (math.inf, -math.inf, math.nan)


def test_that_finite_real_check_rejects_huge_integer():
    huge_x: int = 10**10000
    assert _is_finite_real(huge_x) is False


@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_finite_realness_check_rejects_non_reals(non_real: Any) -> None:
    assert not _is_finite_real(non_real)


@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_finite_realness_check_rejects_non_finite_floats(
    non_finite: float,
) -> None:
    assert not _is_finite_real(non_finite)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_interval_lower_bound_must_be_a_finite_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: float,
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=non_finite, upper=12.7)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_interval_upper_bound_must_be_a_finite_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: float,
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=-3.281, upper=non_finite)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_segment_start_must_be_a_finite_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: float,
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(start=non_finite, end=2.48, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_segment_end_must_be_a_finite_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: float,
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(start=-16.075, end=non_finite, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_interval_lower_bound_must_be_a_real_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=non_real, upper=15.0)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_interval_upper_bound_must_be_a_real_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=-24.801, upper=non_real)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_non_finite_real_is_not_contained_by_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: Any,
) -> None:
    interval = interval_cls(lower=24.801, upper=57.802)
    assert interval._includes(non_finite) is False
    with pytest.raises(TypeError):
        assert non_finite not in interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_non_real_is_not_contained_by_interval(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    interval = interval_cls(lower=24.801, upper=57.802)
    assert interval._includes(non_real) is False
    with pytest.raises(TypeError):
        assert non_real not in interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
def test_that_non_finite_real_is_not_contained_by_segment(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite: Any,
) -> None:
    segment = DirectedSegment.create(
        start=24.801, end=57.802, interval_cls=interval_cls
    )
    with pytest.raises(TypeError):
        assert non_finite not in segment


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_non_real_is_not_contained_by_segment(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    segment = DirectedSegment.create(
        start=24.801, end=57.802, interval_cls=interval_cls
    )
    with pytest.raises(TypeError):
        assert non_real not in segment


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_segment_start_must_be_a_real_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(start=non_real, end=2.48, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize("non_real", NON_REALS)
def test_that_segment_end_must_be_a_real_number(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real: Any,
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(start=-16.075, end=non_real, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "invalid_interval_cls",
    [int, float, str, bool, None, ClosedInterval(lower=0, upper=1)],
)
def test_that_segment_rejects_non_interval_classes(
    invalid_interval_cls: Any,
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(
            start=-5.2,
            end=-10.0,
            interval_cls=invalid_interval_cls,
        )


def test_that_segment_rejects_unsupported_interval_class() -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(
            start=5.2,
            end=10.0,
            interval_cls=HomogeneouslyTerminatedInterval,
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_forward_segment_rejects_being_directly_instantiated_with_reversed_endpoints(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    with pytest.raises(ValueError):
        # shouldn't instantiate by direct calls here anyway
        # but this checks guards against inconsistent end points
        _ForwardSegment(start=100.0, end=45, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_inverted_segment_rejects_being_directly_instantiated_with_forward_ordered_endpoints(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    with pytest.raises(ValueError):
        # shouldn't instantiate by direct calls here anyway
        # but this checks guards against inconsistent end points
        _InvertedSegment(start=-100.0, end=45, interval_cls=interval_cls)


@pytest.mark.parametrize("non_finite", NON_FINITE_FLOATS)
@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_any_interval_asked_if_non_finite_value_lies_within_raises_type_error(
    non_finite: float, interval_cls: type[ClosedInterval] | type[OpenInterval]
) -> None:
    interval = interval_cls(lower=-67.4, upper=17.69)
    with pytest.raises(TypeError):
        _check = non_finite in interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "invalid_type",
    NON_REALS,
)
def test_that_any_interval_asked_if_non_real_instance_lies_within_raises_type_error(
    interval_cls: type[ClosedInterval] | type[OpenInterval], invalid_type: Any
) -> None:
    interval = interval_cls(lower=-81.4, upper=127.6543)
    with pytest.raises(TypeError):
        _check = invalid_type in interval


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "endpoint",
    [
        -1,
        0,
        -77.8,
        34.6,
        -24.5,
        -12.02,
        15,
        143.216,
    ],
)
def test_that_no_interval_be_permitted_to_have_zero_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval], endpoint: float
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=endpoint, upper=endpoint)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_no_interval_be_permitted_to_have_non_finite_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=-sys.float_info.max, upper=sys.float_info.max)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_forward_segment_cannot_be_instantiated_with_non_finite_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(
            start=-sys.float_info.max, end=sys.float_info.max, interval_cls=interval_cls
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_inverted_segment_cannot_be_instantiated_with_non_finite_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(
            start=sys.float_info.max, end=-sys.float_info.max, interval_cls=interval_cls
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "extremum",
    (-sys.float_info.max, sys.float_info.max),
)
def test_that_no_directed_segment_be_created_with_non_finite_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval], extremum: float
) -> None:
    with pytest.raises(ValueError):
        DirectedSegment.create(start=-extremum, end=extremum, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
def test_that_no_directed_segment_be_created_with_non_finite_reciprocal_span(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
) -> None:
    smallest_positive_subnormal = math.nextafter(0.0, 1.0)

    with pytest.raises(ValueError):
        DirectedSegment.create(
            start=0.0, end=smallest_positive_subnormal, interval_cls=interval_cls
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "endpoint",
    [
        -12,
        4,
        0,
        0.0,
        0.002,
        1.5,
        67.2,
        11.09,
        12.309,
        -7.5,
        17.2,
        1.045,
        -15.44,
    ],
)
@pytest.mark.parametrize("segment_cls", [_ForwardSegment, _InvertedSegment])
def test_that_instantiation_of_zero_length_segment_is_refused(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    endpoint: float,
    segment_cls: type[DirectedSegment],
) -> None:
    with pytest.raises(ValueError):
        segment_cls(start=endpoint, end=endpoint, interval_cls=interval_cls)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "endpoint",
    [
        -12,
        4,
        0,
        0.0,
        0.002,
        1.5,
        67.2,
        11.09,
        12.309,
        -7.5,
        17.2,
        1.045,
        -15.44,
    ],
)
def test_that_creation_of_zero_length_segment_is_refused(
    interval_cls: type[ClosedInterval] | type[OpenInterval], endpoint: float
) -> None:
    with pytest.raises(ValueError):
        _segment = DirectedSegment.create(
            start=endpoint, end=endpoint, interval_cls=interval_cls
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "lower, upper",
    [
        (
            -1,
            0,
        ),
        (
            -77.8,
            34.6,
        ),
        (
            -24.5,
            -12.02,
        ),
    ],
)
def test_that_any_interval_types_rejects_misordered_endpoints(
    interval_cls: type[ClosedInterval] | type[OpenInterval], lower: float, upper: float
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=upper, upper=lower)


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "non_finite_bound",
    NON_FINITE_FLOATS,
)
@pytest.mark.parametrize("field", ["start", "end"])
def test_that_forward_segment_field_validator_rejects_non_finite_bounds(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite_bound: Any,
    field: str,
) -> None:
    with pytest.raises(ValueError):
        _ForwardSegment.model_validate(
            {
                "start": 1.0,
                "end": 2.0,
                "interval_cls": interval_cls,
                field: non_finite_bound,
            }
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "non_finite_bound",
    NON_FINITE_FLOATS,
)
@pytest.mark.parametrize("field", ["start", "end"])
def test_that_inverted_segment_field_validator_rejects_non_finite_bounds(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_finite_bound: Any,
    field: str,
) -> None:
    with pytest.raises(ValueError):
        _InvertedSegment.model_validate(
            {
                "start": 1.0,
                "end": -2.0,
                "interval_cls": interval_cls,
                field: non_finite_bound,
            }
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "non_real_bound",
    NON_REALS,
)
@pytest.mark.parametrize("field", ["start", "end"])
def test_that_forward_segment_field_validator_rejects_non_real_bounds(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real_bound: Any,
    field: str,
) -> None:
    with pytest.raises(ValueError):
        _ForwardSegment.model_validate(
            {
                "start": 1.0,
                "end": 2.0,
                "interval_cls": interval_cls,
                field: non_real_bound,
            }
        )


@pytest.mark.parametrize(
    "interval_cls",
    INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "non_real_bound",
    NON_REALS,
)
@pytest.mark.parametrize("field", ["start", "end"])
def test_that_inverted_segment_field_validator_rejects_non_real_bounds(
    interval_cls: type[ClosedInterval] | type[OpenInterval],
    non_real_bound: Any,
    field: str,
) -> None:
    with pytest.raises(ValueError):
        _InvertedSegment.model_validate(
            {
                "start": 1.0,
                "end": -2.0,
                "interval_cls": interval_cls,
                field: non_real_bound,
            }
        )
