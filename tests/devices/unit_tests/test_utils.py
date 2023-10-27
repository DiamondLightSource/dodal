from unittest.mock import MagicMock

import pytest
from ophyd.status import Status

from dodal.devices.utils import run_functions_without_blocking
from dodal.log import LOGGER


class StatusException(Exception):
    pass


def get_bad_status():
    status = Status(obj="Dodal test utils - get good status")
    status.set_exception(StatusException())
    return status


def get_good_status():
    status = Status(obj="Dodal test utils - get good status")
    status.set_finished()
    return status


def test_run_functions_without_blocking_errors_on_invalid_func():
    def bad_func():
        return 5

    with pytest.raises(ValueError):
        run_functions_without_blocking([bad_func], 5)  # type: ignore


def test_full_status_gives_error_if_intermediate_status_fails():
    full_status = run_functions_without_blocking([get_bad_status], 5)
    error = full_status.exception()
    assert error is not None


def test_check_call_back_error_gives_correct_error():
    LOGGER.error = MagicMock()
    returned_status = Status(done=True, success=True)
    with pytest.raises(StatusException):
        returned_status = run_functions_without_blocking([get_bad_status])
        returned_status.wait(0.1)

    assert isinstance(returned_status.exception(), StatusException)

    LOGGER.error.assert_called()


def test_wrap_function_callback():
    dummy_func = MagicMock(return_value=Status(done=True, success=True))
    returned_status = run_functions_without_blocking(
        [lambda: get_good_status(), dummy_func]
    )
    dummy_func.assert_called_once()
    try:
        returned_status.wait(0.1)
    except BaseException:
        pass


def test_wrap_function_callback_errors_on_wrong_return_type():
    dummy_func = MagicMock(return_value=3)
    returned_status = Status(done=True, success=True)
    with pytest.raises(ValueError):
        returned_status = run_functions_without_blocking(
            [lambda: get_good_status(), dummy_func]
        )
    dummy_func.assert_called_once()
    try:
        returned_status.wait(0.1)
    except BaseException:
        pass


def test_status_points_to_provided_device_object():
    expected_obj = MagicMock()
    returned_status = run_functions_without_blocking(
        [get_good_status], associated_obj=expected_obj
    )
    returned_status.wait(0.1)
    assert returned_status.obj == expected_obj
