from unittest.mock import MagicMock

import pytest
from ophyd.status import Status

from dodal.devices.utils import wrap_and_do_funcs
from dodal.log import LOGGER


def get_bad_status():
    status = Status()
    status.set_exception(Exception)
    return status


def get_good_status():
    status = Status()
    status.set_finished()
    return status


def test_wrap_and_do_funcs_errors_on_invalid_func():
    def bad_func():
        return 5

    with pytest.raises(ValueError):
        wrap_and_do_funcs([bad_func], 5)


def test_full_status_gives_error_if_intermediate_status_fails():
    full_status = wrap_and_do_funcs([get_bad_status], 5)
    error = full_status.exception()
    assert error is not None


def test_check_call_back_error_gives_correct_error():
    LOGGER.error = MagicMock()
    wrap_and_do_funcs([get_bad_status])

    wrap_and_do_funcs([get_good_status])
    LOGGER.error.assert_called_once()


def test_wrap_function_callback():
    dummy_func = MagicMock(return_value=Status)
    wrap_and_do_funcs([lambda: get_good_status(), dummy_func])
    dummy_func.assert_called_once
