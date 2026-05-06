"""Provides a checker to determine if a value is within a certain range."""

from pydantic import BaseModel, validate_call


def subordinate_range_test(lower_bound: float, upper_bound: float, x: float) -> bool:
    outside_range = x < lower_bound or x > upper_bound
    return not outside_range


class Range(BaseModel):
    lower_bound: float  # Annotated[float, Field(lt=upper_bound)]
    upper_bound: float  # Annotated[float, Field(gt=lower_bound)]


@validate_call
def is_within_range(
    lower_bound: float,
    upper_bound: float,
    tested_value: float,
) -> bool:
    """Checks if a single value falls between two bounds, a lower (first) and an upper
    (second).

    Args:
        lower_bound (float): the smaller of the two values
        upper_bound (float): the greater of the two values
        tested_value (float): the value to be tested

    Returns:
        outside_range (bool): True if the tested value falls between, or False if not
    """
    # still in progress. Pydantic strangeness. Will fix.
    Range(lower_bound=lower_bound, upper_bound=upper_bound)
    if upper_bound < lower_bound:
        value_error_message_template = (
            "Range upper bound %.4f < lower bound %.4f is an invalid condition"
        )
        value_error_message = value_error_message_template % (
            upper_bound,
            lower_bound,
        )
        raise ValueError(value_error_message)
    else:
        return subordinate_range_test(
            lower_bound,
            upper_bound,
            tested_value,
        )
