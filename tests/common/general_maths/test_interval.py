import math
from typing import Any, Final

import pytest

from dodal.common.general_maths.interval import (
    ClosedInterval,
    ClosedOpenInterval,
    DirectedSegment,
    FloatInterval,
    OpenClosedInterval,
    OpenInterval,
)

ALL_CONCRETE_INTERVAL_TYPES: tuple[type[FloatInterval], ...] = (
    ClosedInterval,
    ClosedOpenInterval,
    OpenClosedInterval,
    OpenInterval,
)

# Happy path


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_all_interval_types_recognise_point_when_unambiguously_within(
    interval_cls: type[FloatInterval], probed_x: float, lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert probed_x in interval


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_directed_segment_can_be_created_when_backed_by_any_interval_type(
    interval_cls: type[FloatInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert isinstance(segment, DirectedSegment)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_all_interval_types_report_correct_span(
    interval_cls: type[FloatInterval], expected_span: float, lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert interval.span == pytest.approx(expected_span)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_directed_segments_report_correct_span(
    interval_cls: type[FloatInterval], expected_span: float, start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment.span == pytest.approx(expected_span)


@pytest.mark.parametrize("interval_cls", ALL_CONCRETE_INTERVAL_TYPES)
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
def test_all_interval_types_recognise_point_when_unambiguously_without(
    interval_cls: type[FloatInterval], probed_x: float, lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    assert probed_x not in interval


@pytest.mark.parametrize("interval_cls", ALL_CONCRETE_INTERVAL_TYPES)
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
def test_segments_recognise_point_when_unambiguously_without(
    interval_cls: type[FloatInterval], probed_x: float, start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert probed_x not in segment


@pytest.mark.parametrize("interval_cls", ALL_CONCRETE_INTERVAL_TYPES)
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
def test_segments_recognise_point_when_unambiguously_within(
    interval_cls: type[FloatInterval], probed_x: float, start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert probed_x in segment


@pytest.mark.parametrize(
    "interval_cls",
    [
        ClosedOpenInterval,
        OpenClosedInterval,
        OpenInterval,
    ],
)
def test_other_interval_types_avoid_hash_collisions_with_closed_interval(
    interval_cls,
) -> None:
    a: int = 4
    b: int = 5
    benchmark = ClosedInterval(lower=a, upper=b)
    other = interval_cls(lower=a, upper=b)
    assert hash(benchmark) != hash(other)


@pytest.mark.parametrize(
    "interval_cls",
    [
        OpenClosedInterval,
        OpenInterval,
    ],
)
def test_other_interval_types_avoid_hash_collisions_with_closed_open_interval(
    interval_cls,
) -> None:
    a: int = 4
    b: int = 5
    benchmark = ClosedOpenInterval(lower=a, upper=b)
    other = interval_cls(lower=a, upper=b)
    assert hash(benchmark) != hash(other)


def test_open_closed_and_open_intervals_do_not_suffer_hash_collisions() -> None:
    a: int = 4
    b: int = 5
    benchmark = OpenClosedInterval(lower=a, upper=b)
    other = OpenInterval(lower=a, upper=b)
    assert hash(benchmark) != hash(other)


@pytest.mark.parametrize("interval_cls", ALL_CONCRETE_INTERVAL_TYPES)
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
def test_all_interval_types_recognise_another_interval_lies_outside(
    interval_cls: type[FloatInterval], lower: float, upper: float
) -> None:
    probe_external_interval = ClosedInterval(lower=101.4, upper=952.93)
    outer_interval = interval_cls(lower=lower, upper=upper)
    assert probe_external_interval not in outer_interval


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_that_all_interval_types_recognise_another_interval_lies_inside(
    interval_cls: type[FloatInterval], lower: float, upper: float
) -> None:
    probe_inner_interval = ClosedInterval(lower=1.4, upper=1.93)
    outer_interval = interval_cls(lower=lower, upper=upper)
    assert probe_inner_interval in outer_interval


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval], lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    initial_span = interval.span
    with pytest.raises(ValueError):
        interval.lower = lower - 5.1
    assert interval.span == pytest.approx(initial_span) and interval.lower == lower


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval], lower: float, upper: float
) -> None:
    interval = interval_cls(lower=lower, upper=upper)
    initial_span = interval.span
    with pytest.raises(ValueError):
        interval.upper = lower + 2.78 * initial_span
    assert interval.span == pytest.approx(initial_span) and interval.upper == upper


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    initial_span = segment.span
    with pytest.raises(ValueError):
        segment.start = start + 1.38 * initial_span
    assert segment.span == pytest.approx(initial_span) and segment.start == start


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    initial_span = segment.span
    with pytest.raises(ValueError):
        segment.end = start - 5.91 * initial_span
    assert segment.span == pytest.approx(initial_span) and segment.end == end


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (11.5, -2.1),
        (617.2, 1.2),
        (91.329, -15.44),
    ],
)
def test_that_segment_is_equal_to_itself(
    interval_cls: type[FloatInterval],
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
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_that_segment_is_not_equal_to_any_other_type(
    interval_cls: type[FloatInterval],
    other: Any,
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    assert segment != other


@pytest.mark.parametrize(
    "interval_cls1",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "interval_cls2",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "start, end",
    [
        (1.5, -2.1),
        (67.2, 1.2),
        (19.379, -15.44),
    ],
)
def test_that_segment_is_equal_to_another_with_same_ends_independent_of_interval_backing(
    interval_cls1: type[FloatInterval],
    interval_cls2: type[FloatInterval],
    start: float,
    end: float,
) -> None:
    segment1 = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls1)
    segment2 = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls2)
    assert segment1 == segment2


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    inverted = ~segment

    def assert_ends_swapped(a: DirectedSegment, b: DirectedSegment) -> bool:
        return bool(a.start == b.end)

    assert assert_ends_swapped(segment, inverted)
    assert assert_ends_swapped(inverted, segment)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
    interval_cls: type[FloatInterval],
    start: float,
    end: float,
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    inverted = ~segment
    assert inverted.span == -(segment.span)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_that_segment_backed_by_any_interval_type_is_not_equal_to_a_different_segment(
    interval_cls: type[FloatInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    swapped = DirectedSegment.create(start=end, end=start, interval_cls=interval_cls)
    assert segment != swapped


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_that_segment_backed_by_any_interval_type_is_not_equal_to_another_with_swapped_ends(
    interval_cls: type[FloatInterval], start: float, end: float
) -> None:
    segment = DirectedSegment.create(start=start, end=end, interval_cls=interval_cls)
    swapped = DirectedSegment.create(start=end, end=start, interval_cls=interval_cls)
    assert segment != swapped


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_that_segment_backed_by_any_interval_type_is_not_equal_to_another_with_distinct_ends(
    interval_cls: type[FloatInterval], c: float, d: float
) -> None:
    a = 5.1
    b = 23.458
    segment1 = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    segment2 = DirectedSegment.create(start=a + c, end=b + d, interval_cls=interval_cls)
    assert segment1 != segment2


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "a, b, x, expected_f",
    [
        (1.5, -2.1, 0.1, 0.38888889),
        (1.5, -2.1, -0.1, 0.44444444),
        (9, 17, 15, 0.75),
        (12.2, 1.8, 15, -0.26923076923),
        (100, 200, 123, 0.23),
        (100, 0, 48, 0.52),
    ],
)
def test_that_inverse_linear_interpolation_gives_expected_fraction(
    interval_cls: type[FloatInterval],
    a: float,
    b: float,
    x: float,
    expected_f: float,
) -> None:
    segment = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    fraction = segment.inverse_linear_interpolated_value(value=x)
    assert fraction == pytest.approx(expected_f)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "a, b, expected_x, f",
    [
        (1.5, -2.1, 0.1, 0.38888889),
        (1.5, -2.1, -0.1, 0.44444444),
        (9, 17, 15, 0.75),
        (12.2, 1.8, 15, -0.26923076923),
        (100, 200, 123, 0.23),
        (100, 0, 48, 0.52),
    ],
)
def test_that_linear_interpolation_converts_parametric_fraction_to_expected_value(
    interval_cls: type[FloatInterval],
    a: float,
    b: float,
    expected_x: float,
    f: float,
) -> None:
    segment = DirectedSegment.create(start=a, end=b, interval_cls=interval_cls)
    x = segment.linear_interpolation_of_fraction(fractional_parameter=f)
    assert x == pytest.approx(x)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "x",
    [
        (1.5),
        (67.2),
        (11.09),
        (12.309),
        (7.5),
        (17.2),
        (1.045),
        (-15.44),
    ],
)
def test_that_zero_length_segment_refuses_to_be_instantiated(
    interval_cls: type[FloatInterval], x: float
) -> None:
    with pytest.raises(ValueError):
        _segment = DirectedSegment.create(start=x, end=x, interval_cls=interval_cls)


# Not sharply testing end points as these tests will be brittle to machine epsilon
# Therefore excluding tests of inclusivity on end points
# also excluding tests of zero length intervals - given those are impractical it's no great loss

# Inauspicious path

NON_NUMERICAL_TYPES: Final[tuple[Any, ...]] = (
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
)


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
)
@pytest.mark.parametrize(
    "invalid_type",
    NON_NUMERICAL_TYPES,
)
def test_that_any_interval_asked_if_invalid_type_lies_within_raises_type_error(
    interval_cls: type[FloatInterval], invalid_type: Any
) -> None:
    interval = interval_cls(lower=-81.4, upper=127.6543)
    with pytest.raises(TypeError):
        _check = invalid_type in interval


@pytest.mark.parametrize(
    "interval_cls",
    ALL_CONCRETE_INTERVAL_TYPES,
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
def test_any_interval_types_rejects_misordered_endpoints(
    interval_cls: type[FloatInterval], lower: float, upper: float
) -> None:
    with pytest.raises(ValueError):
        interval_cls(lower=upper, upper=lower)
