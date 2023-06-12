from unittest.mock import MagicMock

import pytest
from ophyd.status import Status

from dodal.devices.utils import run_functions_without_blocking
from dodal.log import LOGGER


def get_bad_status():
    status = Status()
    status.set_exception(Exception)
    return status


def get_good_status():
    status = Status()
    status.set_finished()
    return status


def test_run_functions_without_blocking_errors_on_invalid_func():
    def bad_func():
        return 5

    with pytest.raises(ValueError):
        run_functions_without_blocking([bad_func], 5)


def test_full_status_gives_error_if_intermediate_status_fails():
    full_status = run_functions_without_blocking([get_bad_status], 5)
    error = full_status.exception()
    assert error is not None


def test_check_call_back_error_gives_correct_error():
    LOGGER.error = MagicMock()
    run_functions_without_blocking([get_bad_status])

    run_functions_without_blocking([get_good_status])
    LOGGER.error.assert_called_once()


def test_wrap_function_callback():
    dummy_func = MagicMock(return_value=Status)
    run_functions_without_blocking([lambda: get_good_status(), dummy_func])
    dummy_func.assert_called_once
