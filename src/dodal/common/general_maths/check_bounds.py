"""Provides a checker to determine if a value is within a certain range."""

from pydantic import BaseModel, StrictFloat, model_validator, validate_call


def subordinate_range_test(
    lower_bound: StrictFloat, upper_bound: StrictFloat, x: StrictFloat
) -> bool:
    outside_range = x < lower_bound or x > upper_bound
    return not outside_range


@validate_call
def is_within_range(
    lower_bound: StrictFloat,
    upper_bound: StrictFloat,
    tested_value: StrictFloat,
) -> bool:
    """Checks if a single value falls between two bounds, a lower (first) and an upper
    (second).

    Args:
        lower_bound (StrictFloat): the smaller of the two values
        upper_bound (StrictFloat): the greater of the two values
        tested_value (StrictFloat): the value to be tested

    Returns:
        outside_range (bool): True if the tested value falls between, or False if not
    """

    class ValueRange(BaseModel):
        lo: StrictFloat
        hi: StrictFloat

        @model_validator(mode="after")
        def validate_bounds(self) -> "ValueRange":
            if self.hi < self.lo:
                raise ValueError(f"Upper bound {self.hi} < Lower bound {self.lo}")
            return self

    ValueRange(lo=lower_bound, hi=upper_bound)
    return subordinate_range_test(
        lower_bound,
        upper_bound,
        tested_value,
    )
