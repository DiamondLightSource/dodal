import threading
from unittest.mock import MagicMock, call, patch

import pytest
from mockito import ANY, mock, verify, when
from ophyd.sim import NullStatus
from ophyd.status import Status

from dodal.devices.detector import DetectorParams, TriggerMode
from dodal.devices.eiger import EigerDetector
from dodal.devices.status import await_value
from dodal.devices.util.epics_util import run_functions_without_blocking
from dodal.log import LOGGER
from dodal.testing_utils import StatusException, constants, get_bad_status


def mock_eiger_odin_statuses(eiger):
    eiger.set_odin_pvs = MagicMock(return_value=NullStatus())
    eiger._wait_for_odin_status = MagicMock(return_value=NullStatus())
    eiger._wait_fan_ready = MagicMock(return_value=NullStatus())


@pytest.fixture
def mock_set_odin_filewriter(mock_eiger: EigerDetector):
    mock_eiger.odin.nodes.clear_odin_errors = MagicMock()
    mock_eiger.odin.check_odin_initialised = MagicMock()
    mock_eiger.odin.check_odin_initialised.return_value = (True, "")
    mock_eiger.odin.file_writer.file_path.put(True)

    def do_set(val: str):
        mock_eiger.odin.meta.file_name.sim_put(val)  # type: ignore
        mock_eiger.odin.file_writer.id.sim_put(val)  # type: ignore
        stat = Status()
        stat.set_finished()
        return stat

    return do_set


@pytest.mark.parametrize(
    "current_energy_ev, request_energy, is_energy_change",
    [
        (100.0, 100.0, False),
        (100.0, 200.0, True),
        (100.0, 50.0, True),
        (100.0, 100.09, False),
        (100.0, 99.91, False),
    ],
)
def test_detector_threshold(
    mock_eiger: EigerDetector,
    current_energy_ev: float,
    request_energy: float,
    is_energy_change: bool,
):
    status_obj = MagicMock()
    when(mock_eiger.cam.photon_energy).get().thenReturn(current_energy_ev)
    when(mock_eiger.cam.photon_energy).set(ANY, timeout=ANY).thenReturn(status_obj)

    returned_status = mock_eiger.set_detector_threshold(request_energy)

    if is_energy_change:
        verify(mock_eiger.cam.photon_energy, times=1).set(request_energy, timeout=ANY)
        assert returned_status == status_obj
    else:
        verify(mock_eiger.cam.photon_energy, times=0).set(ANY, timeout=ANY)
        returned_status.wait(0.1)
        assert returned_status.success


@pytest.mark.parametrize(
    "detector_params, detector_size_constants, beam_xy_converter, expected_error_number",
    [
        (mock(), mock(), mock(), 0),
        (None, mock(), mock(), 1),
        (mock(), None, mock(), 1),
        (None, None, mock(), 1),
        (None, None, None, 1),
        (mock(), None, None, 2),
    ],
)
def test_check_detector_variables(
    mock_eiger: EigerDetector,
    detector_params: DetectorParams,
    detector_size_constants,
    beam_xy_converter,
    expected_error_number,
):
    if detector_params is not None:
        detector_params.beam_xy_converter = beam_xy_converter
        detector_params.detector_size_constants = detector_size_constants

    if expected_error_number != 0:
        with pytest.raises(Exception) as e:
            mock_eiger.set_detector_parameters(detector_params)
        number_of_errors = str(e.value).count("\n") + 1

        assert number_of_errors == expected_error_number
    else:
        try:
            mock_eiger.set_detector_parameters(detector_params)
        except Exception as e:
            assert False, f"exception was raised {e}"


# Tests transition from set_odin_pvs_after_file_writer_set to set_mx_settings_pvs
def test_when_set_odin_pvs_called_then_full_filename_written_and_set_mx_settings_runs(
    mock_eiger: EigerDetector,
):
    expected_full_filename = f"{constants.EIGER_PREFIX}_{constants.EIGER_RUN_NUMBER}"

    unwrapped_funcs = [
        mock_eiger.set_odin_number_of_frame_chunks,
        mock_eiger.set_odin_pvs,
        mock_eiger.set_mx_settings_pvs,
    ]

    status = run_functions_without_blocking(unwrapped_funcs)

    mock_eiger.odin.file_writer.num_frames_chunks.sim_put(1)  # type: ignore
    assert mock_eiger.detector_params is not None
    # Logic for propagating filename is not in fake eiger
    mock_eiger.odin.meta.file_name.sim_put(expected_full_filename)  # type: ignore
    mock_eiger.odin.file_writer.id.sim_put(expected_full_filename)  # type: ignore

    assert (
        mock_eiger.cam.beam_center_x.get()
        != mock_eiger.detector_params.get_beam_position_pixels(
            mock_eiger.detector_params.detector_distance
        )[0]
    )

    status.wait()

    assert mock_eiger.odin.file_writer.file_name.get() == expected_full_filename

    assert (
        mock_eiger.cam.beam_center_x.get()
        == mock_eiger.detector_params.get_beam_position_pixels(
            mock_eiger.detector_params.detector_distance
        )[0]
    )


def test_stage_raises_exception_if_odin_initialisation_status_not_ok(mock_eiger):
    when(mock_eiger.odin.nodes).clear_odin_errors().thenReturn(None)
    expected_error_message = "Test error"
    when(mock_eiger.odin).check_odin_initialised().thenReturn(
        (False, expected_error_message)
    )
    with pytest.raises(
        Exception, match=f"Odin not initialised: {expected_error_message}"
    ):
        mock_eiger.async_stage().wait()


@pytest.mark.parametrize(
    "roi_mode, expected_num_change_roi_calls", [(True, 1), (False, 0)]
)
@patch("dodal.devices.eiger.await_value")
def test_stage_enables_roi_mode_correctly(
    mock_await, mock_eiger, roi_mode, expected_num_change_roi_calls
):
    when(mock_eiger.odin.nodes).clear_odin_errors().thenReturn(None)
    when(mock_eiger.odin).check_odin_initialised().thenReturn((True, ""))

    mock_eiger.detector_params.use_roi_mode = roi_mode
    mock_await.return_value = Status(done=True)
    change_roi_mode_status = Status()
    mock_eiger.change_roi_mode = MagicMock(return_value=change_roi_mode_status)

    returned_status = mock_eiger.async_stage()

    assert mock_eiger.change_roi_mode.call_count == expected_num_change_roi_calls

    # Tidy up async staging
    change_roi_mode_status.set_exception(Exception)
    with pytest.raises(Exception):
        returned_status.wait(0.1)


def test_disable_roi_mode_sets_correct_roi_mode(mock_eiger):
    mock_roi_change = MagicMock()
    mock_eiger.change_roi_mode = mock_roi_change
    mock_eiger.disable_roi_mode()
    mock_roi_change.assert_called_once_with(False)


@pytest.mark.parametrize(
    "roi_mode, expected_detector_dimensions",
    [
        (True, constants.EIGER_DETECTOR_SIZE_CONSTANTS.roi_size_pixels),
        (False, constants.EIGER_DETECTOR_SIZE_CONSTANTS.det_size_pixels),
    ],
)
def test_change_roi_mode_sets_correct_detector_size_constants(
    mock_eiger, roi_mode, expected_detector_dimensions
):
    mock_odin_height_set = MagicMock()
    mock_odin_width_set = MagicMock()
    mock_eiger.odin.file_writer.image_height.set = mock_odin_height_set
    mock_eiger.odin.file_writer.image_width.set = mock_odin_width_set

    mock_eiger.change_roi_mode(roi_mode)
    mock_odin_height_set.assert_called_once_with(
        expected_detector_dimensions.height, timeout=10
    )
    mock_odin_width_set.assert_called_once_with(
        expected_detector_dimensions.width, timeout=10
    )


@pytest.mark.parametrize(
    "roi_mode, expected_cam_roi_mode_call", [(True, 1), (False, 0)]
)
def test_change_roi_mode_sets_cam_roi_mode_correctly(
    mock_eiger, roi_mode, expected_cam_roi_mode_call
):
    mock_cam_roi_mode_set = MagicMock()
    mock_eiger.cam.roi_mode.set = mock_cam_roi_mode_set
    mock_eiger.change_roi_mode(roi_mode)
    mock_cam_roi_mode_set.assert_called_once_with(
        expected_cam_roi_mode_call, timeout=mock_eiger.GENERAL_STATUS_TIMEOUT
    )


# Also tests transition from change ROI to set_detector_threshold
@patch("ophyd.status.Status.__and__")
def test_unsuccessful_true_roi_mode_change_results_in_callback_error(
    mock_and, mock_eiger: EigerDetector
):
    bad_status = Status()
    bad_status.set_exception(StatusException("Failed setting ROI mode True"))
    mock_and.return_value = bad_status
    LOGGER.error = MagicMock()

    unwrapped_funcs = [
        lambda: mock_eiger.change_roi_mode(enable=True),
        lambda: mock_eiger.set_detector_threshold(
            energy=mock_eiger.detector_params.expected_energy_ev
        ),
    ]
    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait()
    LOGGER.error.assert_called()


@patch("ophyd.status.Status.__and__")
def test_unsuccessful_false_roi_mode_change_results_in_callback_error(
    mock_and, mock_eiger: EigerDetector
):
    bad_status = Status()
    bad_status.set_exception(StatusException("Failed setting ROI mode False"))
    mock_and.return_value = bad_status
    LOGGER.error = MagicMock()

    unwrapped_funcs = [
        lambda: mock_eiger.change_roi_mode(enable=False),
        lambda: mock_eiger.set_detector_threshold(
            energy=mock_eiger.detector_params.expected_energy_ev
        ),
    ]
    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait()


@patch("dodal.devices.eiger.EigerOdin.check_odin_state")
def test_bad_odin_state_results_in_unstage_returning_bad_status(
    mock_check_odin_state, mock_eiger: EigerDetector
):
    mock_check_odin_state.return_value = False
    mock_eiger.filewriters_finished = NullStatus()  # type: ignore
    returned_status = mock_eiger.unstage()
    assert returned_status is False


def test_given_failing_odin_when_stage_then_exception_raised(mock_eiger):
    error_contents = "Got an error"
    mock_eiger.odin.nodes.clear_odin_errors = MagicMock()
    mock_eiger.odin.check_odin_initialised = MagicMock()
    mock_eiger.odin.check_odin_initialised.return_value = (False, error_contents)
    with pytest.raises(Exception) as e:
        mock_eiger.async_stage().wait()
    assert error_contents in e.value.__str__()


def set_up_eiger_to_stage_happily(mock_eiger: EigerDetector):
    mock_eiger.odin.nodes.clear_odin_errors = MagicMock()
    mock_eiger.odin.check_odin_initialised = MagicMock(return_value=(True, ""))
    mock_eiger.odin.file_writer.file_path.put(True)


@patch("dodal.devices.eiger.await_value")
def test_stage_runs_successfully(mock_await, mock_eiger: EigerDetector):
    mock_await.return_value = NullStatus()
    set_up_eiger_to_stage_happily(mock_eiger)
    mock_eiger.stage()
    mock_eiger.arming_status.wait(1)  # This should complete long before 1s


@patch("dodal.devices.eiger.await_value")
def test_given_stale_parameters_goes_high_before_callbacks_then_stale_parameters_waited_on(
    mock_await,
    mock_eiger: EigerDetector,
):
    mock_await.return_value = Status(done=True)
    set_up_eiger_to_stage_happily(mock_eiger)

    mock_eiger_odin_statuses(mock_eiger)

    def wait_on_staging():
        st = mock_eiger.async_stage()
        st.wait()

    waiting_status = Status()
    mock_eiger.cam.num_images.set = MagicMock(return_value=waiting_status)

    thread = threading.Thread(target=wait_on_staging, daemon=True)
    thread.start()

    assert thread.is_alive()

    mock_eiger.stale_params.sim_put(1)  # type: ignore
    waiting_status.set_finished()

    assert thread.is_alive()

    mock_eiger.stale_params.sim_put(0)  # type: ignore

    thread.join(0.2)
    assert not thread.is_alive()


# Tests transition from waiting for stale params to _wait_for_odin_status()
def test_when_stage_called_then_odin_started_after_stale_params_goes_low(
    mock_eiger: EigerDetector, mock_set_odin_filewriter
):
    mock_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    mock_eiger.stale_params.sim_put(1)  # type: ignore
    mock_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore
    mock_eiger.odin.meta.active.sim_put(1)  # type: ignore

    unwrapped_funcs = [
        lambda: await_value(mock_eiger.stale_params, 0, 60),
        mock_eiger._wait_for_odin_status,
    ]

    returned_status = run_functions_without_blocking(unwrapped_funcs)

    assert mock_eiger.odin.file_writer.capture.get() == 0

    mock_eiger.stale_params.sim_put(0)  # type: ignore

    await_value(mock_eiger.odin.file_writer.capture, 1).wait(1)
    mock_eiger.odin.meta.ready.sim_put(1)  # type: ignore

    returned_status.wait(0.1)


# Tests transition from _wait_for_odin_status to cam_acquire_set
def test_when_stage_called_then_cam_acquired_on_meta_ready(
    mock_eiger: EigerDetector, mock_set_odin_filewriter
):
    mock_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    mock_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore
    mock_eiger.stale_params.sim_put(0)  # type: ignore
    mock_eiger.odin.meta.active.sim_put(1)  # type: ignore

    unwrapped_funcs = [
        mock_eiger._wait_for_odin_status,
        lambda: mock_eiger.cam.acquire.set(1, timeout=10),
    ]

    returned_status = run_functions_without_blocking(unwrapped_funcs)

    assert mock_eiger.cam.acquire.get() == 0

    mock_eiger.odin.meta.ready.sim_put(1)  # type: ignore

    await_value(mock_eiger.cam.acquire, 1).wait(1)
    returned_status.wait(1)


# Tests transition from _wait_fan_ready to _finish_arm
def test_when_stage_called_then_finish_arm_on_fan_ready(
    mock_eiger: EigerDetector, mock_set_odin_filewriter
):
    mock_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    # Mock this function so arming actually finishes
    mock_eiger.odin.create_finished_status = MagicMock()

    mock_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    mock_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore

    unwrapped_funcs = [mock_eiger._wait_fan_ready, mock_eiger._finish_arm]
    status = run_functions_without_blocking(unwrapped_funcs)

    mock_eiger.odin.meta.ready.sim_put(1)  # type: ignore
    status.wait(5)


@pytest.mark.parametrize(
    "iteration",
    range(10),
)
def test_check_callback_error(mock_eiger: EigerDetector, iteration):
    LOGGER.error = MagicMock()

    # These functions timeout without extra tweaking rather than give us the specific status error for the test
    mock_eiger_odin_statuses(mock_eiger)

    unwrapped_funcs = [
        (
            lambda: mock_eiger.set_detector_threshold(
                energy=mock_eiger.detector_params.expected_energy_ev
            )
        ),
        (mock_eiger.set_cam_pvs),
        (mock_eiger.set_odin_number_of_frame_chunks),
        (mock_eiger.set_odin_pvs),
        (mock_eiger.set_mx_settings_pvs),
        (mock_eiger.set_num_triggers_and_captures),
        (mock_eiger._wait_for_odin_status),
        (lambda: mock_eiger.cam.acquire.set(1, timeout=10)),
        (mock_eiger._wait_fan_ready),
        (mock_eiger._finish_arm),
    ]

    unwrapped_funcs[iteration] = get_bad_status

    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait(timeout=10)
        LOGGER.error.assert_called_once()


def test_given_in_free_run_mode_when_staged_then_triggers_and_filewriter_set_correctly(
    mock_eiger: EigerDetector,
):
    mock_eiger.odin.nodes.clear_odin_errors = MagicMock()
    mock_eiger.odin.check_odin_initialised = MagicMock()
    mock_eiger.odin.check_odin_initialised.return_value = (True, "")
    mock_eiger.odin.file_writer.file_path.put(True)
    mock_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    mock_eiger.set_num_triggers_and_captures()
    assert mock_eiger.cam.num_triggers.get() > mock_eiger.detector_params.num_triggers
    assert mock_eiger.odin.file_writer.num_capture.get() == 0


def test_given_in_free_run_mode_when_unstaged_then_waiting_on_file_writer_to_finish_correctly(
    mock_eiger: EigerDetector,
):
    mock_eiger.filewriters_finished = NullStatus()  # type: ignore

    mock_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    mock_eiger.odin.file_writer.num_captured.sim_put(2000)  # type: ignore
    mock_eiger.odin.check_odin_state = MagicMock(return_value=True)

    mock_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    mock_eiger.unstage()

    assert mock_eiger.odin.meta.stop_writing.get() == 1
    assert mock_eiger.odin.file_writer.capture.get() == 0


def test_given_in_free_run_mode_and_not_all_frames_collected_in_time_when_unstaged_then_odin_stopped_and_exception_thrown(
    mock_eiger: EigerDetector,
):
    mock_eiger.filewriters_finished = NullStatus()  # type: ignore

    mock_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    mock_eiger.odin.file_writer.num_captured.sim_put(1000)  # type: ignore
    mock_eiger.odin.check_odin_state = MagicMock(return_value=True)

    mock_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    mock_eiger.ALL_FRAMES_TIMEOUT = 0.1
    with pytest.raises(Exception):
        mock_eiger.unstage()

    assert mock_eiger.odin.meta.stop_writing.get() == 1
    assert mock_eiger.odin.file_writer.capture.get() == 0


def test_if_arming_in_progress_then_stage_waits_for_completion(
    mock_eiger: EigerDetector, mock_set_odin_filewriter
):
    mock_eiger.arming_status = Status()

    thread = threading.Thread(target=mock_eiger.stage, daemon=True)
    thread.start()

    assert thread.is_alive()

    mock_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    mock_eiger.cam.acquire.sim_put(1)  # type: ignore

    mock_eiger.arming_status.set_finished()

    thread.join(0.01)


def test_if_eiger_isnt_armed_then_stage_calls_async_stage(mock_eiger: EigerDetector):
    mock_eiger.async_stage = MagicMock()
    mock_eiger.odin.fan.ready.sim_put(0)  # type: ignore
    mock_eiger.stage()
    mock_eiger.async_stage.assert_called_once()


def test_if_eiger_is_armed_then_stage_does_nothing(mock_eiger: EigerDetector):
    mock_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    mock_eiger.cam.acquire.sim_put(1)  # type: ignore
    mock_eiger.async_stage = MagicMock()
    mock_eiger.stage()
    mock_eiger.async_stage.assert_not_called()


def test_given_detector_arming_when_unstage_then_wait_for_arming_to_finish(
    mock_eiger: EigerDetector,
):
    mock_eiger.filewriters_finished = NullStatus()  # type:ignore

    mock_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    mock_eiger.odin.file_writer.num_captured.sim_put(2000)  # type: ignore
    mock_eiger.odin.check_odin_state = MagicMock(return_value=True)

    mock_eiger.arming_status = Status()
    mock_eiger.arming_status.wait = MagicMock()
    mock_eiger.unstage()
    mock_eiger.arming_status.wait.assert_called_once()


def test_given_detector_arming_status_failed_when_unstage_then_detector_still_disarmed(
    mock_eiger: EigerDetector,
):
    mock_eiger.cam.acquire.sim_put(1)  # type: ignore

    mock_eiger.arming_status = get_bad_status()
    with pytest.raises(Exception):
        mock_eiger.unstage()

    assert mock_eiger.cam.acquire.get() == 0


def test_given_not_all_frames_done_when_eiger_stopped_then_do_not_wait_for_frames_but_disarm(
    mock_eiger: EigerDetector,
):
    mock_eiger.disarm_detector = MagicMock()
    mock_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    mock_eiger.odin.file_writer.num_captured.sim_put(10)  # type: ignore

    mock_eiger.stop()

    mock_eiger.disarm_detector.assert_called()


def lambda_in_calls(f, mock_calls):
    for _call in mock_calls:
        if hasattr(_call.args[0], "__name__") and _call.args[0].__name__ == "<lambda>":
            if f._extract_mock_name() in _call.args[0].__code__.co_names:
                return True
    return False


@patch("dodal.devices.util.epics_util.call_func")
@patch("dodal.devices.eiger.await_value", name="await_value")
def test_unwrapped_arm_chain_functions_are_not_called_outside_util(
    await_value: MagicMock,
    call_func: MagicMock,
    mock_eiger: EigerDetector,
):
    mock_eiger.odin.stop = MagicMock(return_value=Status(done=True, success=True))
    mock_eiger.detector_params.use_roi_mode = True

    call_func.return_value = NullStatus()
    mock_eiger.enable_roi_mode = MagicMock(name="enable_roi_mode")
    mock_eiger.set_detector_threshold = MagicMock(name="set_detector_threshold")
    mock_eiger.set_cam_pvs = MagicMock(name="set_cam_pvs")
    mock_eiger.set_odin_number_of_frame_chunks = MagicMock(
        name="set_odin_number_of_frame_chunks"
    )
    mock_eiger.set_odin_pvs = MagicMock(name="set_odin_pvs")
    mock_eiger.set_mx_settings_pvs = MagicMock(name="set_mx_settings_pvs")
    mock_eiger.set_num_triggers_and_captures = MagicMock(
        name="set_num_triggers_and_captures"
    )
    mock_eiger._wait_for_odin_status = MagicMock(name="_wait_for_odin_status")
    mock_eiger.cam.acquire.set = MagicMock(name="set")
    mock_eiger._wait_fan_ready = MagicMock(name="_wait_fan_ready")
    mock_eiger._finish_arm = MagicMock(name="_finish_arm")

    mock_eiger.do_arming_chain()

    funcs = [
        mock_eiger.odin.stop,
        mock_eiger.enable_roi_mode,
        mock_eiger.set_detector_threshold,
        mock_eiger.set_cam_pvs,
        mock_eiger.set_odin_number_of_frame_chunks,
        mock_eiger.set_odin_pvs,
        mock_eiger.set_mx_settings_pvs,
        mock_eiger.set_num_triggers_and_captures,
        mock_eiger._wait_for_odin_status,
        mock_eiger.cam.acquire.set,
        mock_eiger._wait_fan_ready,
        mock_eiger._finish_arm,
        await_value,
    ]

    for f in funcs:
        f.assert_not_called()
        assert call(f) in call_func.mock_calls or lambda_in_calls(
            f, call_func.mock_calls
        )


@patch("ophyd.status.StatusBase.wait")
def test_stop_eiger_waits_for_status_functions_to_complete(
    mock_wait: MagicMock, mock_eiger: EigerDetector
):
    mock_eiger.stop()
    mock_wait.assert_called()


@pytest.mark.parametrize(
    "enable_dev_shm, expected_set",
    [
        (True, 1),
        (False, 0),
    ],
)
@patch("dodal.devices.eiger.await_value")
def test_given_dev_shm_when_stage_then_correctly_enable_disable_dev_shm(
    mock_await,
    enable_dev_shm: bool,
    expected_set: int,
    mock_eiger: EigerDetector,
):
    mock_await.return_value = NullStatus()
    set_up_eiger_to_stage_happily(mock_eiger)

    mock_eiger.detector_params.enable_dev_shm = enable_dev_shm  # type:ignore

    mock_eiger.stage()

    assert mock_eiger.odin.fan.dev_shm_enable.get() == expected_set


def test_when_eiger_is_stopped_then_dev_shm_disabled(mock_eiger: EigerDetector):
    mock_eiger.odin.fan.dev_shm_enable.sim_put(1)  # type:ignore

    mock_eiger.stop()

    assert mock_eiger.odin.fan.dev_shm_enable.get() == 0
