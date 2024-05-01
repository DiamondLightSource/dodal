from functools import partial
from typing import Callable

from ophyd import Component, Device, EpicsSignal
from ophyd.status import Status, StatusBase

from dodal.devices.status import await_value
from dodal.log import LOGGER


def epics_signal_put_wait(pv_name: str, wait: float = 3.0) -> Component[EpicsSignal]:
    """Creates a `Component` around an `EpicsSignal` that waits for a callback on a put.

    Args:
        pv_name (str): The name of the PV for the `EpicsSignal`
        wait (str, optional): The timeout to wait for a callback. Defaults to 3.0.

    Returns:
        EpicsSignal: An EpicsSignal that will wait for a callback.
    """
    return Component(EpicsSignal, pv_name, put_complete=True, write_timeout=wait)


def run_functions_without_blocking(
    functions_to_chain: list[Callable[[], StatusBase]],
    timeout: float = 60.0,
    associated_obj: Device | None = None,
) -> Status:
    """Creates and initiates an asynchronous chaining of functions which return a status

    Usage:
    This function can be used to take a series of status-returning functions and run
    them all sequentially and in the background by making use of callbacks. It also
    ensures exceptions on each returned status are propagated

    Args:
    functions_to_chain( list(function - > StatusBase) ): A list of functions which each
                                                            return a status object
    associated_obj (Device | None): The device that should be associated with the
                                        returned status

    Returns:
    Status: A status object which is marked as complete once all of the Status objects
    returned by the unwrapped functions have completed.
    """

    # The returned status - marked as finished at the end of the callback chain. If any
    # intermediate statuses have an exception, the full_status will timeout.
    full_status = Status(obj=associated_obj, timeout=timeout)

    def closing_func(old_status: Status):
        if old_status.exception() is not None:
            set_global_exception_and_log(old_status)
        else:
            full_status.set_finished()

    # Wrap each function by first checking the previous status and attaching a callback
    # to the next function in the chain
    def wrap_func(
        old_status: Status, current_func: Callable[[], StatusBase], next_func
    ):
        if old_status.exception() is not None:
            set_global_exception_and_log(old_status)
            return

        status = call_func(current_func)

        if not isinstance(status, StatusBase):
            LOGGER.error(
                f"wrap_func attempted to wrap {current_func} when it does not return a Status"
            )
            raise ValueError(f"{current_func} does not return a Status")

        status.add_callback(next_func)

    def set_global_exception_and_log(status: Status):
        error = status.exception()
        full_status.set_exception(error)
        # So full_status can also be checked for any errors
        LOGGER.error(f"Status {status} has failed with error {error}")

    # Each wrapped function needs to attach its callback to the subsequent wrapped
    # function, therefore wrapped_funcs list needs to be created in reverse order

    wrapped_funcs = []
    wrapped_funcs.append(
        partial(
            wrap_func,
            current_func=functions_to_chain[-1],
            next_func=closing_func,
        )
    )

    # Wrap each function in reverse
    for num, func in enumerate(list(reversed(functions_to_chain))[1:-1]):
        wrapped_funcs.append(
            partial(
                wrap_func,
                current_func=func,
                next_func=wrapped_funcs[-1],
            )
        )

    starting_status = Status(done=True, success=True)

    # Initiate the chain of functions
    wrap_func(starting_status, functions_to_chain[0], wrapped_funcs[-1])
    return full_status


def call_func(func: Callable[[], StatusBase]) -> StatusBase:
    return func()


class SetWhenEnabled(Device):
    """A device that sets the proc field of a PV when it becomes enabled."""

    proc = Component(EpicsSignal, ".PROC")
    disp = Component(EpicsSignal, ".DISP")

    def set(self, proc: int) -> Status:
        return run_functions_without_blocking(
            [
                lambda: await_value(self.disp, 0),
                lambda: self.proc.set(proc),
            ]
        )
