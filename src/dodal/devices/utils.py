from functools import partial
from typing import Callable

from ophyd import Component, EpicsSignal
from ophyd.status import Status

from dodal.log import LOGGER


def epics_signal_put_wait(pv_name: str, wait: float = 1.0) -> EpicsSignal:
    """Creates a `Component` around an `EpicsSignal` that waits for a callback on a put.

    Args:
        pv_name (str): The name of the PV for the `EpicsSignal`
        wait (str, optional): The timeout to wait for a callback. Defaults to 1.0.

    Returns:
        EpicsSignal: An EpicsSignal that will wait for a callback.
    """
    return Component(EpicsSignal, pv_name, put_complete=True, write_timeout=wait)


def wrap_and_do_funcs(
    unwrapped_funcs: list[Callable[[], Status]],
    timeout: float = 60.0,
) -> Status:
    """Creates and initiates an asynchronous chaining of functions which return a status.

    Usage:
    This function can be used to convert a series of blocking status functions to being asynchronous
    by making use of callbacks. It also checks for exceptions on each returned status
    For example, instead of blocking on status.wait(), the code will continue running until the status
    is marked as finished

    Args:
    unwrapped_funcs( list(function - > Status) ): A list of functions which each return a status object

    Returns:
    Status: A status object which is marked as complete once all of the Status objects returned by the
    unwrapped functions have completed.
    """

    # Wrap each function by first checking the previous status and attaching a callback to the next
    # function in the chain
    def wrap_func(old_status, current_func: Callable[[], Status], next_func):
        check_callback_error(old_status)
        LOGGER.info(f"Doing {current_func.__name__}")
        status = current_func()
        status.add_callback(next_func)

    def check_callback_error(status: Status):
        error = status.exception()
        if error is not None:
            LOGGER.error(f"{status} has failed with error {error}")
            raise error  # This raised error is caught within status.py

    # The returned status - marked as finished at the end of the callback chain. If any
    # intermediate statuses have an exception, the full_status will timeout.
    full_status = Status(timeout=timeout)

    starting_status = Status()
    starting_status.set_finished()

    # Each wrapped function needs to attach its callback to the subsequent wrapped function, therefore
    # wrapped_funcs list needs to be created in reverse order

    # Once the series of functions have finished with successful statuses, the final action is to mark
    # the full_status as finished

    wrapped_funcs = list()
    wrapped_funcs.append(
        partial(
            wrap_func,
            current_func=unwrapped_funcs[-1],
            next_func=lambda: full_status.set_finished(),
        )
    )

    # Wrap each function in reverse
    for num, func in enumerate(list(reversed(unwrapped_funcs))[1:-1]):
        wrapped_funcs.append(
            partial(
                wrap_func,
                current_func=func,
                next_func=wrapped_funcs[-1],
            )
        )

    # Initiate the chain of functions
    wrap_func(starting_status, unwrapped_funcs[0], wrapped_funcs[-1])
    return full_status
