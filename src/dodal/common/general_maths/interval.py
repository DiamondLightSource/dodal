import math
from abc import ABC, abstractmethod
from functools import cached_property
from numbers import Real
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
    model_validator,
)

from dodal.common.general_maths.arithmetic_conversions import get_straight_line_y


def _is_finite_real(x: Any) -> bool:
    if isinstance(x, bool) or not isinstance(x, Real):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:
        # Very large values can trigger overflow on the isfinite check
        return False


class HomogeneouslyTerminatedInterval(BaseModel, ABC):
    """Immutable interval of finite floating-point values.

    Invariants:
        - Both endpoints must be finite.
        - The lower endpoint must be strictly less than the upper endpoint.
        - Zero-span intervals are not supported.
        - Endpoints are either, both included (Closed) or both excluded (Open) per sub-class.

    Attributes:
        lower: The lower endpoint defining the interval.
        upper: The upper endpoint defining the interval.
    """

    lower: float
    upper: float

    model_config = ConfigDict(frozen=True)
    __hash__ = None

    @computed_field
    @property
    def span(self) -> float:
        return self.upper - self.lower

    @field_validator("lower", "upper", mode="before")
    @classmethod
    def validate_fields(cls, bound: Any) -> float:

        if _is_finite_real(bound):
            return bound
        else:
            raise ValueError(
                f"Interval bound {bound} is not numerical, finite and real - must be all of these."
            )

    @model_validator(mode="after")
    def _ensure_valid(self) -> "HomogeneouslyTerminatedInterval":
        if not math.isfinite(self.span):
            raise ValueError("Interval span must be finite.")
        if self.span > 0.0:
            return self
        msg = (
            f"Interval is inverted! Lower endpoint {self.lower} cannot be greater than the upper {self.upper}."
            if self.span < 0.0
            else "Intervals of zero length are not supported."
        )
        raise ValueError(msg)

    @abstractmethod
    def _includes(self, x: float) -> bool:
        """Internal method to impose the specific interval type definition, endpoints are closed or open.

        Args:
            x: the value to be checked against the interval endpoints.

        Returns:
            True if the interval includes the input value.
        """
        ...

    def _contains_interval(
        self,
        other_interval: "HomogeneouslyTerminatedInterval",
    ) -> bool:
        """Return whether this interval contains the entirety of another interval."""
        if other_interval is self:
            # This interval contains itself
            return True
        if other_interval.lower in self and other_interval.upper in self:
            # Both endpoints of the other interval are included in this one
            return True
        if self._fails_to_enclose(other_interval):
            return False
        return self._contains_shared_boundaries(other_interval)

    def _contains_shared_boundaries(
        self,
        other_interval: "HomogeneouslyTerminatedInterval",
    ) -> bool:
        """A contained interval may share an excluded boundary with its container,
        but must not include a boundary excluded by its container.
        """
        other_lower = other_interval.lower
        if other_lower in other_interval and other_lower not in self:
            return False
        other_upper = other_interval.upper
        if other_upper in other_interval and other_upper not in self:
            return False
        return True

    def _fails_to_enclose(
        self,
        other_interval: "HomogeneouslyTerminatedInterval",
    ) -> bool:
        """Return True if the bounds of the other interval lie clearly beyond the bounds of self."""
        return other_interval.lower < self.lower or other_interval.upper > self.upper

    def __contains__(self, item: object) -> bool:
        if isinstance(item, bool):
            raise TypeError(
                "Checking for booleans inside a HomogeneousFloatInterval is not supported."
                "Neither booleans nor strings are coerced into floating points by any Interval class."
            )
        if isinstance(item, Real):
            if not _is_finite_real(item):
                raise TypeError(
                    "Expecting to only test whether a floating point value and integer "
                    "or another interval instance lie within this interval."
                )
            else:
                return self._includes(float(item))
        if isinstance(item, HomogeneouslyTerminatedInterval):
            return self._contains_interval(item)
        else:
            raise TypeError(
                f"Objects of type {type(item)} cannot be found inside a FloatInterval."
            )

    def __eq__(self, item: object) -> bool:
        if self is item:
            return True
        if not isinstance(item, HomogeneouslyTerminatedInterval):
            return NotImplemented
        else:
            return (
                type(self) is type(item)
                and self.lower == item.lower
                and self.upper == item.upper
            )


class ClosedInterval(HomogeneouslyTerminatedInterval):
    """Interval with inclusive end points."""

    def _includes(self, x: float) -> bool:
        if not _is_finite_real(x):
            return False
        excluded: bool = x < self.lower or x > self.upper
        return not excluded


class OpenInterval(HomogeneouslyTerminatedInterval):
    """Interval with exclusive end points."""

    def _includes(self, x: float) -> bool:
        if not _is_finite_real(x):
            return False
        return self.lower < x < self.upper


class DirectedSegment(BaseModel, ABC):
    """Abstract base for directed segments Generic against HomogeneousFloatInterval type.

    Attributes:
        interval_cls type of the backing FloatInterval
        start: the begin of the directional segment
        end: the end of the directional segment

    Note:
        Unlike intervals, the start and end can be in either or order.
    """

    interval_cls: type[HomogeneouslyTerminatedInterval]

    start: float
    end: float

    model_config = ConfigDict(frozen=True)
    __hash__ = None

    @field_validator("interval_cls")
    @classmethod
    def _validate_interval_class(
        cls, value: type[HomogeneouslyTerminatedInterval]
    ) -> type[HomogeneouslyTerminatedInterval]:
        if value not in (ClosedInterval, OpenInterval):
            raise ValueError(
                f"Unsupported interval class: {value!r}. "
                "Expected ClosedInterval or OpenInterval."
            )
        return value

    @field_validator("start", "end", mode="before")
    @classmethod
    def _validate_fields(cls, bound: Any) -> float:
        if _is_finite_real(bound):
            return bound
        else:
            raise ValueError(
                f"Segment bound {bound} is not numerical, finite and real - must be all of these."
            )

    @model_validator(mode="after")
    def _validate_span_aspects(self) -> "DirectedSegment":
        if self.start == self.end:
            raise ValueError("Zero-length segments are not supported.")
        # Non-finite span is checked by interval
        if not _is_finite_real(self._reciprocal_of_span):
            raise ValueError("Segment span reciprocal must be finite.")
        return self

    @cached_property
    def _interval(self) -> HomogeneouslyTerminatedInterval:
        """Backing interval is decoupled from the orientation of the Segment."""
        return self.interval_cls(
            lower=min(self.start, self.end), upper=max(self.start, self.end)
        )

    @cached_property
    def _reciprocal_of_span(self) -> float:
        return 1.0 / self.span

    @property
    @abstractmethod
    def span(self) -> float: ...

    def linear_interpolation_of_fraction(self, *, fractional_parameter: float) -> float:
        """Linear interpolation of fraction of span away from start, to general float."""
        return get_straight_line_y(
            line_offset=self.start, line_gradient=self.span, x=fractional_parameter
        )

    def inverse_linear_interpolated_value(self, *, value: float) -> float:
        """Inverse linear interpolation converts value to fractions of span away from start."""
        return get_straight_line_y(
            line_offset=-self.start * self._reciprocal_of_span,
            line_gradient=self._reciprocal_of_span,
            x=value,
        )

    @abstractmethod
    def __invert__(self) -> "DirectedSegment": ...

    def __contains__(self, item: object) -> bool:
        return item in self._interval

    def __eq__(self, item: object) -> bool:
        if self is item:
            return True
        if not isinstance(item, DirectedSegment):
            return NotImplemented
        return (
            self.start == item.start
            and self.end == item.end
            and self._interval == item._interval
        )

    @classmethod
    def create(
        cls,
        start: float,
        end: float,
        interval_cls: type[HomogeneouslyTerminatedInterval] = ClosedInterval,
    ) -> "DirectedSegment":
        if not _is_finite_real(start) or not _is_finite_real(end):
            raise ValueError("Segment endpoints must be finite real numbers.")
        if start == end:
            raise ValueError(
                "Segment end points may not coincide - as that would give zero length."
            )
        segment_cls = _InvertedSegment if start > end else _ForwardSegment
        return segment_cls(start=start, end=end, interval_cls=interval_cls)


class _ForwardSegment(DirectedSegment):
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _validate_direction(self) -> "_ForwardSegment":
        """Validates directionality matches name in case instantiation by-passes factory create in parent class."""
        if self.start > self.end:
            raise ValueError("_ForwardSegment has been instantiated in reverse.")
        return self

    @property
    def span(self) -> float:
        return self._interval.span

    def __invert__(self) -> "DirectedSegment":
        return _InvertedSegment(
            start=self.end,
            end=self.start,
            interval_cls=self.interval_cls,
        )


class _InvertedSegment(DirectedSegment):
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _validate_direction(self) -> "_InvertedSegment":
        """Validates directionality matches name in case instantiation by-passes factory create in parent class."""
        if self.start < self.end:
            raise ValueError(
                "_InvertedSegment has been instantiated in forward direction."
            )
        return self

    @property
    def span(self) -> float:
        return -self._interval.span

    def __invert__(self) -> "DirectedSegment":
        return _ForwardSegment(
            start=self.end,
            end=self.start,
            interval_cls=self.interval_cls,
        )
