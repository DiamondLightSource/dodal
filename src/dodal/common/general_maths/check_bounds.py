def subordinate_range_test(lower_bound: float, upper_bound: float, x: float):
    outside_range = x < lower_bound or x > upper_bound
    return not outside_range


def is_within_range(lower_bound: float, upper_bound: float, tested_value: float):
    """Checks if a single value falls between two bounds, a lower (first) and an upper
    (second).

    Args:
        lower_bound (float): the smaller of the two values
        upper_bound (float): the greater of the two values
        tested_value (float): the value to be tested

    Returns:
        outside_range (bool): True if the tested value falls between, or False if not
    """
    # TODO check if we need to use pydantic for this.
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
