from pydantic import BaseModel, ConfigDict, StrictFloat, model_validator


class FloatInterval(BaseModel):
    """Base class for immutable range of floating point values.

    N.B. Specific sub classes cover different end point types ( closed / open ).

    Attributes:
        lower: The lower endpoint defining the interval.
        upper: The upper endpoint defining the interval.
    """

    lower: StrictFloat
    upper: StrictFloat

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _ensure_order(self) -> "FloatInterval":
        if self.lower > self.upper:
            _msg = f"Interval is inverted! Lower endpoint {self.lower} cannot be greater than the upper {self.upper}."
            raise ValueError(_msg)
        return self

    def _includes(self, x: float) -> bool:
        """Internal method to impose the specific interval type definition, endpoints are closed or open.

        Args:
            x: the value to be checked against the interval endpoints.

        Returns:
            True if the interval includes the input value.
        """
        ...

    def __contains__(self, item: object) -> bool:
        if isinstance(item, (int, float)):
            return self._includes(item)
        if isinstance(item, FloatInterval):
            return item.lower in self and item.upper in self
        return False

    def __hash__(self) -> int:
        # Generate a stable hash based on the interval boundaries and class type
        # (ensuring ClosedInterval vs OpenInterval with same numbers hash differently)
        _hashable_innards = (type(self), self.lower, self.upper)
        return hash(_hashable_innards)


class ClosedInterval(FloatInterval):
    """Interval with inclusive end points."""

    def _includes(self, x: float) -> bool:
        return self.lower <= x <= self.upper


class ClosedOpenInterval(FloatInterval):
    """Interval with inclusive lower endpoint and exclusive upper endpoint."""

    def _includes(self, x: float) -> bool:
        return self.lower <= x < self.upper


class OpenInterval(FloatInterval):
    """Interval with exclusive end points."""

    def _includes(self, x: float) -> bool:
        return self.lower < x < self.upper


class OpenClosedInterval(FloatInterval):
    """Interval with exclusive lower endpoint and inclusive upper endpoint."""

    def _includes(self, x: float) -> bool:
        return self.lower < x <= self.upper
