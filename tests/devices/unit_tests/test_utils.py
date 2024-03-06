from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import NullStatus, make_fake_device
from ophyd.status import Status
from ophyd.utils.errors import StatusTimeoutError, WaitTimeoutError

from dodal.devices.util.epics_util import SetWhenEnabled, run_functions_without_blocking
from dodal.log import LOGGER, GELFTCPHandler, logging, set_up_all_logging_handlers


class StatusException(Exception):
    pass


def discard_status(status: Status):
    try:
        status.wait(0.1)
    except BaseException:
        pass


def reset_logs():
    for handler in LOGGER.handlers:
        handler.close()
    LOGGER.handlers = []
    mock_graylog_handler_class = MagicMock(spec=GELFTCPHandler)
    mock_graylog_handler_class.return_value.level = logging.DEBUG
    with patch("dodal.log.GELFTCPHandler", mock_graylog_handler_class):
        set_up_all_logging_handlers(LOGGER, Path("./tmp/dev"), "dodal.log", True, 10000)
    return mock_graylog_handler_class


def get_bad_status():
    status = Status(obj="Dodal test utils - get bad status")
    status.set_exception(StatusException())
    return status


def get_hanging_status():
    status = Status(obj="Dodal test utils - get hanging status")
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
    dummy_func = MagicMock(return_value=Status())
    returned_status = run_functions_without_blocking([lambda: NullStatus(), dummy_func])
    discard_status(returned_status)
    dummy_func.assert_called_once()


def test_wrap_function_callback_errors_on_wrong_return_type(caplog):
    reset_logs()

    def get_good_status():
        status = Status(obj="Dodal test utils - get good status", timeout=0.1)
        status.set_finished()
        return status

    dummy_func = MagicMock(return_value=3)
    returned_status = Status(done=True, success=True)
    returned_status = run_functions_without_blocking(
        [lambda: get_good_status(), dummy_func], timeout=0.05
    )
    with pytest.raises(StatusTimeoutError):
        returned_status.wait(0.2)
    assert returned_status.done is True
    assert returned_status.success is False

    dummy_func.assert_called_once()

    assert "does not return a Status" in caplog.text


def test_status_points_to_provided_device_object():
    expected_obj = MagicMock()
    returned_status = run_functions_without_blocking(
        [NullStatus], associated_obj=expected_obj
    )
    returned_status.wait(0.1)
    assert returned_status.obj == expected_obj


def test_given_disp_high_when_set_SetWhenEnabled_then_proc_not_set_until_disp_low():
    signal: SetWhenEnabled = make_fake_device(SetWhenEnabled)(name="test")
    signal.disp.sim_put(1)  # type: ignore
    signal.proc.set = MagicMock(return_value=Status(done=True, success=True))

    status = signal.set(1)
    signal.proc.set.assert_not_called()
    signal.disp.sim_put(0)  # type: ignore
    status.wait()
    signal.proc.set.assert_called_once()


def test_if_one_status_errors_then_later_functions_not_called():
    tester = MagicMock(return_value=Status(done=True, success=True))
    status_calls = [
        NullStatus,
        NullStatus,
        get_bad_status,
        NullStatus,
        tester,
    ]
    expected_obj = "TEST OBJECT"
    returned_status = run_functions_without_blocking(
        status_calls, associated_obj=expected_obj
    )
    with pytest.raises(StatusException):
        returned_status.wait(0.1)
    assert returned_status.done
    tester.assert_not_called()


def test_if_one_status_pending_then_later_functions_not_called():
    tester = MagicMock(return_value=Status(done=True, success=True))
    pending_status = Status()
    status_calls = [
        NullStatus,
        NullStatus,
        lambda: pending_status,
        NullStatus,
        tester,
    ]
    expected_obj = "TEST OBJECT"
    returned_status = run_functions_without_blocking(
        status_calls, associated_obj=expected_obj
    )
    with pytest.raises(WaitTimeoutError):
        returned_status.wait(0.1)
    tester.assert_not_called()
    pending_status.set_exception(StatusException)
    with pytest.raises(StatusException):
        returned_status.wait(0.1)
    tester.assert_not_called()
