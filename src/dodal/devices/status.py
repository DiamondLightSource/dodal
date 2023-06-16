from typing import Any, TypeVar, Union

from ophyd.status import Status, SubscriptionStatus

T = TypeVar("T")


def await_value(
    subscribable: Any, expected_value: T, timeout: Union[None, int] = None
) -> Union[Status, SubscriptionStatus]:
    def value_is(value, **_):
        return value == expected_value

    if subscribable.get() == expected_value:
        status = Status()
        status.set_finished()
        return status

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)
