from asyncio import CancelledError, create_task, sleep
from contextlib import asynccontextmanager

from dodal.log import LOGGER


@asynccontextmanager
async def periodic_reminder(
    message: str = "Waiting",
    schedule: tuple[tuple[int | float, int | None], ...] = (  # seconds, frequency
        (1, 3),
        (5, 3),
        (60, 5),
        (300, 5),
        (1800, 5),
        (3600, None),
    ),
):
    """Periodically logs a message according to a schedule with increasing delays.

    Args:
        message: The message the user wants to output through logging.
        schedule: A tuple list of tuples consisting of (int|float, int|None).
            A sequence of (delay_seconds, count) pairs defining the logging intervals.
            - delay_seconds is the number of seconds to wait between logs.
            - count is how many times to log at this interval. If count is None, it logs indefinitely at that delay.
    """

    async def _log_loop():
        for delay, count in schedule:
            n = 0
            while count is None or n < count:
                LOGGER.info(message)
                await sleep(delay)
                n += 1

    task = create_task(_log_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except CancelledError:
            pass
