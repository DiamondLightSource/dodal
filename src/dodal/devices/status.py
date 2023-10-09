from typing import Any, TypeVar, Union

from ophyd.status import SubscriptionStatus

T = TypeVar("T")


def await_value(
    subscribable: Any, expected_value: T, timeout: Union[None, int] = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value == expected_value

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)


# Returns a status which is completed when the subscriptable contains a value within the expected_value list
def await_value_in_list(
    subscribable: Any, expected_value: list, timeout: Union[None, int] = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value in expected_value

    if not isinstance(expected_value, list):
        raise TypeError(f"expected value {expected_value} is not a list")
    else:
        return SubscriptionStatus(subscribable, value_is, timeout=timeout)
