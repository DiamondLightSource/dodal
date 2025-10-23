import asyncio
import threading
import time
from random import random
from threading import Thread

import pytest


@pytest.fixture
async def event_loop_fuzzing():
    """
    This fixture can be used to try and detect / reproduce intermittent test failures
    caused by race conditions and timing issues, which are often difficult to replicate
    due to caching etc. causing timing to be different on a development machine compared
    to when the test runs in CI.

    It works by attaching a fuzzer to the current event loop which randomly schedules
    a fixed delay into the event loop thread every few milliseconds. The idea is that
    over a number of iterations, there should be sufficient timing variation introduced
    that the failure can be reproduced.

    Examples:
        Example usage:
    >>> import pytest
    >>> # repeat the test a number of times
    >>> @pytest.mark.parametrize("i", range(0, 100))
    ... async def my_unreliable_test(i, event_loop_fuzzing):
    ...     # Do some stuff in here
    ...     ...
    """
    fuzz_probability = 0.05
    fuzz_delay_s = 0.05
    fuzz_period_s = 0.001
    stop_running = threading.Event()
    event_loop = asyncio.get_running_loop()

    def delay(finished_event: threading.Event):
        time.sleep(fuzz_delay_s)  # noqa: TID251
        finished_event.set()

    def fuzz():
        while not stop_running.is_set():
            if random() < fuzz_probability:
                delay_is_finished = threading.Event()
                event_loop.call_soon_threadsafe(delay, delay_is_finished)
                delay_is_finished.wait()

            time.sleep(fuzz_period_s)  # noqa: TID251

    fuzzer_thread = Thread(group=None, target=fuzz, name="Event loop fuzzer")
    fuzzer_thread.start()
    try:
        yield None
    finally:
        stop_running.set()
        fuzzer_thread.join()
