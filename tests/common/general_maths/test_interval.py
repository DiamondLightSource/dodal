import pytest

from dodal.common.general_maths.interval import (
    ClosedInterval,
    ClosedOpenInterval,
    FloatInterval,
    OpenClosedInterval,
    OpenInterval,
)

# Happy path


@pytest.mark.parametrize(
    "_interval_cls",
    [ClosedInterval, ClosedOpenInterval, OpenClosedInterval, OpenInterval],
)
@pytest.mark.parametrize(
    "_probed_x, _lower, _upper",
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
def test_all_interval_types_recognise_point_when_unamiguously_within(
    _interval_cls: type[FloatInterval], _probed_x: float, _lower: float, _upper: float
) -> None:
    interval = _interval_cls(lower=_lower, upper=_upper)
    assert _probed_x in interval


@pytest.mark.parametrize(
    "_interval_cls",
    [ClosedInterval, ClosedOpenInterval, OpenClosedInterval, OpenInterval],
)
@pytest.mark.parametrize(
    "_probed_x, _lower, _upper",
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
def test_all_interval_types_recognise_point_when_unamiguously_without(
    _interval_cls: type[FloatInterval], _probed_x: float, _lower: float, _upper: float
) -> None:
    interval = _interval_cls(lower=_lower, upper=_upper)
    assert _probed_x not in interval


@pytest.mark.parametrize(
    "_interval_cls",
    [
        ClosedOpenInterval,
        OpenClosedInterval,
        OpenInterval,
    ],
)
def test_other_interval_types_avoid_hash_collisions_with_closed_interval(
    _interval_cls,
) -> None:
    a: int = 4
    b: int = 5
    _benchmark = ClosedInterval(lower=a, upper=b)
    _other = _interval_cls(lower=a, upper=b)
    assert hash(_benchmark) != hash(_other)


@pytest.mark.parametrize(
    "_interval_cls",
    [
        OpenClosedInterval,
        OpenInterval,
    ],
)
def test_other_interval_types_avoid_hash_collisions_with_closed_open_interval(
    _interval_cls,
) -> None:
    a: int = 4
    b: int = 5
    _benchmark = ClosedOpenInterval(lower=a, upper=b)
    _other = _interval_cls(lower=a, upper=b)
    assert hash(_benchmark) != hash(_other)


def test_open_closed_and_open_intervals_do_not_suffer_hash_collisions() -> None:
    a: int = 4
    b: int = 5
    _benchmark = OpenClosedInterval(lower=a, upper=b)
    _other = OpenInterval(lower=a, upper=b)
    assert hash(_benchmark) != hash(_other)


@pytest.mark.parametrize(
    "_interval_cls",
    [ClosedInterval, ClosedOpenInterval, OpenClosedInterval, OpenInterval],
)
@pytest.mark.parametrize(
    "_lower, _upper",
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
    _interval_cls: type[FloatInterval], _lower: float, _upper: float
) -> None:
    _probe_external_interval = ClosedInterval(lower=101.4, upper=952.93)
    _outer_interval = _interval_cls(lower=_lower, upper=_upper)
    assert _probe_external_interval not in _outer_interval


@pytest.mark.parametrize(
    "_interval_cls",
    [ClosedInterval, ClosedOpenInterval, OpenClosedInterval, OpenInterval],
)
@pytest.mark.parametrize(
    "_lower, _upper",
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
def test_all_interval_types_recognise_another_interval_lies_inside(
    _interval_cls: type[FloatInterval], _lower: float, _upper: float
) -> None:
    _probe_inner_interval = ClosedInterval(lower=1.4, upper=1.93)
    _outer_interval = _interval_cls(lower=_lower, upper=_upper)
    assert _probe_inner_interval in _outer_interval


# Not sharply testing end points as these tests will be brittle to machine epsilon
# Therefore excluding tests of inclusivity on end points
# also excluding tests of zero length intervals - given those are impractical it's no great loss

# Inauspicious path


@pytest.mark.parametrize(
    "_interval_cls",
    [ClosedInterval, ClosedOpenInterval, OpenClosedInterval, OpenInterval],
)
@pytest.mark.parametrize(
    "_lower, _upper",
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
    _interval_cls: type[FloatInterval], _lower: float, _upper: float
) -> None:
    with pytest.raises(ValueError):
        _interval_cls(lower=_upper, upper=_lower)
