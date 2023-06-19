from typing import Any, Collection, TypeVar, Union

from ophyd.status import SubscriptionStatus

T = TypeVar("T")


def await_value(
    subscribable: Any, expected_value: T, timeout: Union[None, int] = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        if type(expected_value) == list:
            return value in expected_value
        else:
            return value == expected_value

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)


# Returns a status which is completed when the subscriptable contains a value within the expected_value list
def await_value_in_list(
    subscribable: Any, expected_value: Collection[Any], timeout: Union[None, int] = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        if type(expected_value) == list:
            return value in expected_value
        else:
            raise TypeError(f"{expected_value} is not a Collection type")

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)
