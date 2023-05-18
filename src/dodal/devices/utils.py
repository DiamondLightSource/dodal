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


# --------- CHAIN CALLBACK AND WRAPPING LOGIC----------------
def wrap_and_do_funcs(unwrapped_funcs):
    full_status = Status()  # NOTE: same function as self.arming_status (dont need both)
    starting_status = Status()
    starting_status.set_finished()

    wrapped_funcs = list()
    wrapped_funcs.append(
        partial(
            wrapped_func,
            current_func=unwrapped_funcs[-1],
            next_func=lambda: full_status.set_finished(),
        )
    )
    for num, func in enumerate(list(reversed(unwrapped_funcs))[1:-1]):
        wrapped_funcs.append(
            partial(
                wrapped_func,
                current_func=func,
                next_func=wrapped_funcs[-1],
            )
        )

    wrapped_func(starting_status, unwrapped_funcs[0], wrapped_funcs[-1])
    return full_status


def wrapped_func(old_status, current_func: Callable[[], Status], next_func):
    check_callback_error(old_status)
    LOGGER.info(f"Doing {current_func.__name__}")
    status = current_func()
    status.add_callback(next_func)


def check_callback_error(status: Status):
    error = status.exception()
    if error is not None:
        LOGGER.error(f"{status} has failed with error {error}")
        raise error


# --------- CHAIN CALLBACK AND WRAPPING LOGIC----------------
