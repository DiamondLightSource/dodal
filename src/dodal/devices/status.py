from typing import Any, TypeVar, Union

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
