from threading import Timer
from typing import Any, TypeVar

from ophyd.status import SubscriptionStatus

from dodal.log import LOGGER

T = TypeVar("T")


class WarningSubscriptionStatus(SubscriptionStatus):
    def __init__(
        self,
        device,
        callback,
        event_type=None,
        timeout=None,
        settle_time=None,
        run=True,
        warn_at=None,
        warning_extra_msg="",
    ):
        """SubscriptionStatus which logs a warning if the time taken is longer than
        warn_at seconds. Appends warning_extra_msg to the log message"""
        super().__init__(device, callback, event_type, timeout, settle_time, run)
        if warn_at:
            self._warning_timer = Timer(
                warn_at,
                lambda: LOGGER.warning(
                    f"Status {self} took more than {warn_at} seconds to complete! {warning_extra_msg}"
                ),
            )
            self._warning_timer.start()
        else:
            self._warning_timer = None

    def set_finished(self):
        if self._warning_timer and not self._warning_timer.finished:
            self._warning_timer.cancel()
        return super().set_finished()


def await_value(
    subscribable: Any, expected_value: T, timeout: None | int = None
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value == expected_value

    return SubscriptionStatus(subscribable, value_is, timeout=timeout)


def await_value_and_warn_if_long(
    subscribable: Any,
    expected_value: T,
    timeout: None | int = None,
    warn_at=None,
    warning_extra_msg="",
) -> SubscriptionStatus:
    def value_is(value, **_):
        return value == expected_value

    return WarningSubscriptionStatus(
        subscribable,
        value_is,
        timeout=timeout,
        warn_at=warn_at,
        warning_extra_msg=warning_extra_msg,
    )


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
