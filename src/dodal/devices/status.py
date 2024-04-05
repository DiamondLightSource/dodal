from typing import Any, TypeVar

from ophyd.status import SubscriptionStatus

T = TypeVar("T")


def await_value(
    subscribable: Any, expected_value: T, timeout: None | int = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value == expected_value

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)


def await_value_in_list(
    subscribable: Any, expected_value: list, timeout: None | int = None
) -> SubscriptionStatus:
    """Returns a status which is completed when the subscriptable contains a value
    within the expected_value list"""

    def value_is(value, **_):
        return value in expected_value

    if not isinstance(expected_value, list):
        raise TypeError(f"expected value {expected_value} is not a list")
    else:
        return SubscriptionStatus(subscribable, value_is, timeout=timeout)


def await_approx_value(
    subscribable: Any,
    expected_value: T,
    deadband: float = 1e-09,
    timeout: None | int = None,
) -> SubscriptionStatus:
    def value_is_approx(value, **_):
        return abs(value - expected_value) <= deadband

    return SubscriptionStatus(subscribable, value_is_approx, timeout=timeout)
