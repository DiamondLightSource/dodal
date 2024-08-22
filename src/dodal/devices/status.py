from typing import Any

from ophyd.status import SubscriptionStatus


def await_value(
    subscribable: Any, expected_value: object, timeout: None | int = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value == expected_value

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)
