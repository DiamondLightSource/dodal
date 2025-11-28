from ophyd_async.core import WatchableAsyncStatus, Watcher

from dodal.log import LOGGER

Number = int | float


class _LogOnPercentageProgressWatcher(Watcher[Number]):
    def __init__(
        self,
        status: WatchableAsyncStatus[Number],
        message_prefix: str,
        percent_interval: Number = 25,
    ):
        self.percent_interval = percent_interval
        self._current_percent_interval = 0
        self.message_prefix = message_prefix
        if self.percent_interval <= 0:
            raise ValueError(
                f"Percent interval on class _LogOnPercentageProgressWatcher must be a positive number, but received {self.percent_interval}"
            )
        status.watch(self)

    def __call__(
        self,
        current: Number | None = None,
        initial: Number | None = None,
        target: Number | None = None,
        name: str | None = None,
        unit: str | None = None,
        precision: int | None = None,
        fraction: float | None = None,
        time_elapsed: float | None = None,
        time_remaining: float | None = None,
    ):
        if (
            isinstance(current, Number)
            and isinstance(target, Number)
            and isinstance(initial, Number)
            and target != initial
        ):
            current_percent = int(((current - initial) / (target - initial)) * 100)
            if (
                current_percent
                >= (self._current_percent_interval + 1) * self.percent_interval
            ):
                LOGGER.info(f"{self.message_prefix}: {current_percent}%")
                self._current_percent_interval = (
                    current_percent // self.percent_interval
                )


def log_on_percentage_complete(
    status: WatchableAsyncStatus[int | float],
    message_prefix: str,
    percent_interval: int = 25,
):
    """
    Add watcher to a WatchableAsyncStatus status which will periodically log a message based on percentage completion

    Args:
        status: A WatchableAsyncStatus. For example, Ophyd-async produces this status from a Motor.set method

        message_prefix: The string at the start of each of the produced logging messages

        percent_interval: How often to produce logging message, in terms of percentage completion
        of the status.

    Note that when using with Bluesky plan stubs you will need to cast the status (as of
    Bluesky v1.14.2), since a Bluesky status doesn't use generics - see https://github.com/bluesky/bluesky/issues/1948.

    When running Bluesky plans using an interactive terminal, it is better to use the standard bluesky progress
    bar instead of this function. See https://blueskyproject.io/bluesky/main/progress-bar.html#progress-bar

    Example usage within a Bluesky plan:
    yield from bps.kickoff(my_detector)
    status = yield from bps.complete(my_detector, group="collection complete")
    status = cast(WatchableAsyncStatus, status)
    log_on_percentage_complete(status, "Data collection triggers received", 10)
    yield from bps.wait("collection complete")

    """
    _LogOnPercentageProgressWatcher(status, message_prefix, percent_interval)
