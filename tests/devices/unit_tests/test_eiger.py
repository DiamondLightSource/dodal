# type: ignore # Eiger will soon be ophyd-async https://github.com/DiamondLightSource/dodal/issues/700
import threading
from pathlib import Path
from unittest.mock import ANY, MagicMock, Mock, call, create_autospec, patch

import pytest
from ophyd.sim import NullStatus, make_fake_device
from ophyd.status import Status
from ophyd.utils import UnknownStatusFailure

from conftest import failed_status
from dodal.devices.detector import DetectorParams, TriggerMode
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE
from dodal.devices.eiger import AVAILABLE_TIMEOUTS, EigerDetector
from dodal.devices.status import await_value
from dodal.devices.util.epics_util import run_functions_without_blocking
from dodal.log import LOGGER

TEST_DETECTOR_SIZE_CONSTANTS = EIGER2_X_16M_SIZE

TEST_EXPECTED_ENERGY = 100.0
TEST_EXPOSURE_TIME = 1.0
TEST_PREFIX = "test"
TEST_RUN_NUMBER = 0
TEST_DETECTOR_DISTANCE = 1.0
TEST_OMEGA_START = 0.0
TEST_OMEGA_INCREMENT = 1.0
TEST_NUM_IMAGES_PER_TRIGGER = 1
TEST_NUM_TRIGGERS = 2000
TEST_USE_ROI_MODE = False
TEST_DET_DIST_TO_BEAM_CONVERTER_PATH = "tests/devices/unit_tests/test_lookup_table.txt"


class StatusException(Exception):
    pass


@pytest.fixture
def params(tmp_path: Path) -> DetectorParams:
    return DetectorParams(
        expected_energy_ev=TEST_EXPECTED_ENERGY,
        exposure_time_s=TEST_EXPOSURE_TIME,
        directory=str(tmp_path),
        prefix=TEST_PREFIX,
        run_number=TEST_RUN_NUMBER,
        detector_distance=TEST_DETECTOR_DISTANCE,
        omega_start=TEST_OMEGA_START,
        omega_increment=TEST_OMEGA_INCREMENT,
        num_images_per_trigger=TEST_NUM_IMAGES_PER_TRIGGER,
        num_triggers=TEST_NUM_TRIGGERS,
        use_roi_mode=TEST_USE_ROI_MODE,
        det_dist_to_beam_converter_path=TEST_DET_DIST_TO_BEAM_CONVERTER_PATH,
        detector_size_constants=TEST_DETECTOR_SIZE_CONSTANTS.det_type_string,
    )


@pytest.fixture
def fake_eiger(request, params: DetectorParams):
    FakeEigerDetector: EigerDetector = make_fake_device(EigerDetector)
    fake_eiger: EigerDetector = FakeEigerDetector.with_params(
        params=params, name=f"test fake Eiger: {request.node.name}"
    )
    return fake_eiger


def mock_eiger_odin_statuses(eiger):
    eiger.set_odin_pvs = MagicMock(return_value=finished_status())
    eiger._wait_for_odin_status = MagicMock(return_value=finished_status())
    eiger._wait_fan_ready = MagicMock(return_value=finished_status())


def finished_status():
    status = Status()
    status.set_finished()
    return status


def get_bad_status(exception=StatusException):
    status = Status()
    status.set_exception(exception)
    return status


@pytest.fixture
def mock_set_odin_filewriter(fake_eiger: EigerDetector):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)

    def do_set(val: str):
        fake_eiger.odin.meta.file_name.sim_put(val)  # type: ignore
        fake_eiger.odin.file_writer.id.sim_put(val)  # type: ignore
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
    fake_eiger: EigerDetector,
    current_energy_ev: float,
    request_energy: float,
    is_energy_change: bool,
):
    status_obj = MagicMock()

    fake_eiger.cam.photon_energy.get = create_autospec(
        fake_eiger.cam.photon_energy.get, return_value=current_energy_ev
    )
    fake_eiger.cam.photon_energy.set = Mock(return_value=status_obj)

    returned_status = fake_eiger.set_detector_threshold(request_energy)

    if is_energy_change:
        fake_eiger.cam.photon_energy.set.assert_called_once_with(ANY, timeout=ANY)
        assert returned_status == status_obj
    else:
        fake_eiger.cam.photon_energy.set.assert_not_called()
        returned_status.wait(0.1)
        assert returned_status.success


@pytest.mark.parametrize(
    "detector_params, detector_size_constants, beam_xy_converter, expected_error_number",
    [
        (Mock(), Mock(), Mock(), 0),
        (None, Mock(), Mock(), 1),
        (Mock(), None, Mock(), 1),
        (None, None, Mock(), 1),
        (None, None, None, 1),
        (Mock(), None, None, 2),
    ],
)
def test_check_detector_variables(
    fake_eiger: EigerDetector,
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
            fake_eiger.set_detector_parameters(detector_params)
        number_of_errors = str(e.value).count("\n") + 1

        assert number_of_errors == expected_error_number
    else:
        try:
            fake_eiger.set_detector_parameters(detector_params)
        except Exception as e:
            raise AssertionError(f"exception was raised {e}") from e


# Tests transition from set_odin_pvs_after_file_writer_set to set_mx_settings_pvs
def test_when_set_odin_pvs_called_then_full_filename_written_and_set_mx_settings_runs(
    fake_eiger: EigerDetector,
):
    expected_full_filename = f"{TEST_PREFIX}_{TEST_RUN_NUMBER}"

    unwrapped_funcs = [
        fake_eiger.set_odin_number_of_frame_chunks,
        fake_eiger.set_odin_pvs,
        fake_eiger.set_mx_settings_pvs,
    ]

    status = run_functions_without_blocking(unwrapped_funcs)

    fake_eiger.odin.file_writer.num_frames_chunks.sim_put(1)  # type: ignore
    assert fake_eiger.detector_params is not None
    # Logic for propagating filename is not in fake eiger
    fake_eiger.odin.meta.file_name.sim_put(expected_full_filename)  # type: ignore
    fake_eiger.odin.file_writer.id.sim_put(expected_full_filename)  # type: ignore

    assert (
        fake_eiger.cam.beam_center_x.get()
        != fake_eiger.detector_params.get_beam_position_pixels(
            fake_eiger.detector_params.detector_distance
        )[0]
    )

    status.wait()

    assert fake_eiger.odin.file_writer.file_name.get() == expected_full_filename

    assert (
        fake_eiger.cam.beam_center_x.get()
        == fake_eiger.detector_params.get_beam_position_pixels(
            fake_eiger.detector_params.detector_distance
        )[0]
    )


def test_stage_raises_exception_if_odin_initialisation_status_not_ok(fake_eiger):
    fake_eiger.odin.nodes.clear_odin_errors = Mock(return_value=None)
    expected_error_message = "Test error"
    fake_eiger.odin.wait_for_odin_initialised = Mock(
        return_value=(False, expected_error_message)
    )
    with pytest.raises(
        Exception, match=f"Odin not initialised: {expected_error_message}"
    ):
        fake_eiger.async_stage().wait()


@pytest.mark.parametrize(
    "roi_mode, expected_num_change_roi_calls, expected_exception",
    [(True, 1, "Test Exception 2"), (False, 0, "Test Exception 1")],
)
@patch("dodal.devices.eiger.await_value")
def test_stage_enables_roi_mode_correctly(
    mock_await, fake_eiger, roi_mode, expected_num_change_roi_calls, expected_exception
):
    fake_eiger.odin.nodes.clear_odin_errors = Mock(return_value=None)
    fake_eiger.odin.wait_for_odin_initialised = Mock(return_value=(True, ""))

    fake_eiger.detector_params.use_roi_mode = roi_mode
    mock_await.return_value = failed_status(UnknownStatusFailure("Test Exception"))
    change_roi_mode_status = Status()
    fake_eiger.change_roi_mode = MagicMock(return_value=change_roi_mode_status)

    returned_status = fake_eiger.async_stage()

    assert fake_eiger.change_roi_mode.call_count == expected_num_change_roi_calls

    # Tidy up async staging
    change_roi_mode_status.set_exception(UnknownStatusFailure("Test Exception 2"))
    with pytest.raises(UnknownStatusFailure) as e:
        returned_status.wait(0.1)
        assert e.args[0] == expected_exception


def test_disable_roi_mode_sets_correct_roi_mode(fake_eiger):
    mock_roi_change = MagicMock()
    fake_eiger.change_roi_mode = mock_roi_change
    fake_eiger.disable_roi_mode()
    mock_roi_change.assert_called_once_with(False)


@pytest.mark.parametrize(
    "roi_mode, expected_detector_dimensions",
    [
        (True, TEST_DETECTOR_SIZE_CONSTANTS.roi_size_pixels),
        (False, TEST_DETECTOR_SIZE_CONSTANTS.det_size_pixels),
    ],
)
def test_change_roi_mode_sets_correct_detector_size_constants(
    fake_eiger, roi_mode, expected_detector_dimensions
):
    mock_odin_height_set = MagicMock()
    mock_odin_width_set = MagicMock()
    fake_eiger.odin.file_writer.image_height.set = mock_odin_height_set
    fake_eiger.odin.file_writer.image_width.set = mock_odin_width_set

    fake_eiger.change_roi_mode(roi_mode)
    mock_odin_height_set.assert_called_once_with(
        expected_detector_dimensions.height, timeout=ANY
    )
    mock_odin_width_set.assert_called_once_with(
        expected_detector_dimensions.width, timeout=ANY
    )


@pytest.mark.parametrize(
    "roi_mode, expected_cam_roi_mode_call", [(True, 1), (False, 0)]
)
def test_change_roi_mode_sets_cam_roi_mode_correctly(
    fake_eiger, roi_mode, expected_cam_roi_mode_call
):
    mock_cam_roi_mode_set = MagicMock()
    fake_eiger.cam.roi_mode.set = mock_cam_roi_mode_set
    fake_eiger.change_roi_mode(roi_mode)
    mock_cam_roi_mode_set.assert_called_once_with(
        expected_cam_roi_mode_call, timeout=fake_eiger.timeouts.general_status_timeout
    )


# Also tests transition from change ROI to set_detector_threshold
@patch("ophyd.status.Status.__and__")
def test_unsuccessful_true_roi_mode_change_results_in_callback_error(
    mock_and, fake_eiger: EigerDetector
):
    bad_status = Status()
    bad_status.set_exception(StatusException("Failed setting ROI mode True"))
    mock_and.return_value = bad_status
    LOGGER.error = MagicMock()

    unwrapped_funcs = [
        lambda: fake_eiger.change_roi_mode(enable=True),
        lambda: fake_eiger.set_detector_threshold(
            energy=fake_eiger.detector_params.expected_energy_ev
        ),
    ]
    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait()
    LOGGER.error.assert_called()


@patch("ophyd.status.Status.__and__")
def test_unsuccessful_false_roi_mode_change_results_in_callback_error(
    mock_and, fake_eiger: EigerDetector
):
    bad_status = Status()
    bad_status.set_exception(StatusException("Failed setting ROI mode False"))
    mock_and.return_value = bad_status
    LOGGER.error = MagicMock()

    unwrapped_funcs = [
        lambda: fake_eiger.change_roi_mode(enable=False),
        lambda: fake_eiger.set_detector_threshold(
            energy=fake_eiger.detector_params.expected_energy_ev
        ),
    ]
    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait()


@patch("dodal.devices.eiger.EigerOdin.check_and_wait_for_odin_state")
def test_bad_odin_state_results_in_unstage_returning_bad_status(
    mock_check_and_wait_for_odin_state, fake_eiger: EigerDetector
):
    mock_check_and_wait_for_odin_state.return_value = False
    happy_status = Status()
    happy_status.set_finished()
    fake_eiger.filewriters_finished = happy_status
    returned_status = fake_eiger.unstage()
    assert returned_status is False


def test_given_failing_odin_when_stage_then_exception_raised(fake_eiger):
    error_contents = "Got an error"
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised = MagicMock(
        return_value=(False, error_contents)
    )
    with pytest.raises(Exception) as e:
        fake_eiger.async_stage().wait()
    assert error_contents in e.value.__str__()


def set_up_eiger_to_stage_happily(fake_eiger: EigerDetector):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised = MagicMock(return_value=(True, ""))
    fake_eiger.odin.file_writer.file_path.put(True)


@patch("dodal.devices.eiger_odin.await_value")
@patch("dodal.devices.eiger.await_value")
def test_stage_runs_successfully(
    mock_eiger_await, mock_eiger_odin_await, fake_eiger: EigerDetector
):
    mock_eiger_await.return_value = finished_status()
    mock_eiger_odin_await.return_value = finished_status()
    set_up_eiger_to_stage_happily(fake_eiger)
    fake_eiger.stage()
    fake_eiger.arming_status.wait(1)  # This should complete long before 1s


def test_given_stale_parameters_goes_high_before_callbacks_then_stale_parameters_waited_on(
    fake_eiger: EigerDetector,
):
    set_up_eiger_to_stage_happily(fake_eiger)

    mock_eiger_odin_statuses(fake_eiger)

    def wait_on_staging():
        st = fake_eiger.async_stage()
        st.wait()

    waiting_status = Status()
    fake_eiger.cam.num_images.set = MagicMock(return_value=waiting_status)

    thread = threading.Thread(target=wait_on_staging, daemon=True)
    thread.start()

    assert thread.is_alive()

    fake_eiger.stale_params.sim_put(1)  # type: ignore
    waiting_status.set_finished()

    assert thread.is_alive()

    fake_eiger.stale_params.sim_put(0)  # type: ignore

    thread.join(0.2)
    assert not thread.is_alive()


# Tests transition from waiting for stale params to _wait_for_odin_status()
def test_when_stage_called_then_odin_started_after_stale_params_goes_low(
    fake_eiger: EigerDetector, mock_set_odin_filewriter
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    fake_eiger.stale_params.sim_put(1)  # type: ignore
    fake_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore
    fake_eiger.odin.meta.active.sim_put(1)  # type: ignore

    unwrapped_funcs = [
        lambda: await_value(fake_eiger.stale_params, 0, 60),
        fake_eiger._wait_for_odin_status,
    ]

    returned_status = run_functions_without_blocking(unwrapped_funcs)

    assert fake_eiger.odin.file_writer.capture.get() == 0

    fake_eiger.stale_params.sim_put(0)  # type: ignore

    await_value(fake_eiger.odin.file_writer.capture, 1).wait(1)
    fake_eiger.odin.meta.ready.sim_put(1)  # type: ignore

    returned_status.wait(0.1)


# Tests transition from _wait_for_odin_status to cam_acquire_set
def test_when_stage_called_then_cam_acquired_on_meta_ready(
    fake_eiger: EigerDetector, mock_set_odin_filewriter
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    fake_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore
    fake_eiger.stale_params.sim_put(0)  # type: ignore
    fake_eiger.odin.meta.active.sim_put(1)  # type: ignore

    unwrapped_funcs = [
        fake_eiger._wait_for_odin_status,
        lambda: fake_eiger.cam.acquire.set(1, timeout=10),
    ]

    returned_status = run_functions_without_blocking(unwrapped_funcs)

    assert fake_eiger.cam.acquire.get() == 0

    fake_eiger.odin.meta.ready.sim_put(1)  # type: ignore

    await_value(fake_eiger.cam.acquire, 1).wait(1)
    returned_status.wait(1)


# Tests transition from _wait_fan_ready to _finish_arm
def test_when_stage_called_then_finish_arm_on_fan_ready(
    fake_eiger: EigerDetector, mock_set_odin_filewriter
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    # Mock this function so arming actually finishes
    fake_eiger.odin.create_finished_status = MagicMock()

    fake_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    fake_eiger.odin.file_writer.capture.sim_put(0)  # type: ignore

    unwrapped_funcs = [fake_eiger._wait_fan_ready, fake_eiger._finish_arm]
    status = run_functions_without_blocking(unwrapped_funcs)

    fake_eiger.odin.meta.ready.sim_put(1)  # type: ignore
    status.wait(5)


@pytest.mark.parametrize(
    "iteration",
    range(10),
)
def test_check_callback_error(fake_eiger: EigerDetector, iteration):
    LOGGER.error = MagicMock()

    # These functions timeout without extra tweaking rather than give us the specific status error for the test
    mock_eiger_odin_statuses(fake_eiger)

    unwrapped_funcs = [
        (
            lambda: fake_eiger.set_detector_threshold(
                energy=fake_eiger.detector_params.expected_energy_ev
            )
        ),
        (fake_eiger.set_cam_pvs),
        (fake_eiger.set_odin_number_of_frame_chunks),
        (fake_eiger.set_odin_pvs),
        (fake_eiger.set_mx_settings_pvs),
        (fake_eiger.set_num_triggers_and_captures),
        (fake_eiger._wait_for_odin_status),
        (lambda: fake_eiger.cam.acquire.set(1, timeout=10)),
        (fake_eiger._wait_fan_ready),
        (fake_eiger._finish_arm),
    ]

    unwrapped_funcs[iteration] = get_bad_status

    with pytest.raises(StatusException):
        run_functions_without_blocking(unwrapped_funcs).wait(timeout=10)
        LOGGER.error.assert_called_once()


def test_given_in_free_run_mode_when_staged_then_triggers_and_filewriter_set_correctly(
    fake_eiger: EigerDetector,
):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised = MagicMock()
    fake_eiger.odin.wait_for_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)
    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.set_num_triggers_and_captures()
    assert fake_eiger.cam.num_triggers.get() > fake_eiger.detector_params.num_triggers
    assert fake_eiger.odin.file_writer.num_capture.get() == 0


def test_given_in_free_run_mode_when_unstaged_then_waiting_on_file_writer_to_finish_correctly(
    fake_eiger: EigerDetector,
):
    fake_eiger.filewriters_finished = finished_status()

    fake_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    fake_eiger.odin.file_writer.num_captured.sim_put(2000)  # type: ignore
    fake_eiger.odin.check_and_wait_for_odin_state = MagicMock(return_value=True)

    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.unstage()

    assert fake_eiger.odin.meta.stop_writing.get() == 1
    assert fake_eiger.odin.file_writer.capture.get() == 0


def test_given_in_free_run_mode_and_not_all_frames_collected_in_time_when_unstaged_then_odin_stopped_and_exception_thrown(
    fake_eiger: EigerDetector,
):
    fake_eiger.filewriters_finished = finished_status()

    fake_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    fake_eiger.odin.file_writer.num_captured.sim_put(1000)  # type: ignore
    fake_eiger.odin.check_and_wait_for_odin_state = MagicMock(return_value=True)

    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.timeouts.all_frames_timeout = 0.1
    with pytest.raises(TimeoutError):
        fake_eiger.unstage()

    assert fake_eiger.odin.meta.stop_writing.get() == 1
    assert fake_eiger.odin.file_writer.capture.get() == 0


def test_if_arming_in_progress_then_stage_waits_for_completion(
    fake_eiger: EigerDetector, mock_set_odin_filewriter
):
    fake_eiger.arming_status = Status()

    thread = threading.Thread(target=fake_eiger.stage, daemon=True)
    thread.start()

    assert thread.is_alive()

    fake_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    fake_eiger.cam.acquire.sim_put(1)  # type: ignore

    fake_eiger.arming_status.set_finished()

    thread.join(0.01)


def test_if_eiger_isnt_armed_then_stage_calls_async_stage(fake_eiger: EigerDetector):
    fake_eiger.async_stage = MagicMock()
    fake_eiger.odin.fan.ready.sim_put(0)  # type: ignore
    fake_eiger.stage()
    fake_eiger.async_stage.assert_called_once()


def test_if_eiger_is_armed_then_stage_does_nothing(fake_eiger: EigerDetector):
    fake_eiger.odin.fan.ready.sim_put(1)  # type: ignore
    fake_eiger.cam.acquire.sim_put(1)  # type: ignore
    fake_eiger.async_stage = MagicMock()
    fake_eiger.stage()
    fake_eiger.async_stage.assert_not_called()


def test_given_detector_arming_when_unstage_then_wait_for_arming_to_finish(
    fake_eiger: EigerDetector,
):
    fake_eiger.filewriters_finished = finished_status()

    fake_eiger.odin.file_writer.capture.sim_put(1)  # type: ignore
    fake_eiger.odin.file_writer.num_captured.sim_put(2000)  # type: ignore
    fake_eiger.odin.check_and_wait_for_odin_state = MagicMock(return_value=True)

    fake_eiger.arming_status = Status()
    fake_eiger.arming_status.wait = MagicMock()
    fake_eiger.unstage()
    fake_eiger.arming_status.wait.assert_called_once()


def test_given_detector_arming_status_failed_when_unstage_then_detector_still_disarmed(
    fake_eiger: EigerDetector,
):
    fake_eiger.odin.check_and_wait_for_odin_state = MagicMock(return_value=True)
    fake_eiger.cam.acquire.sim_put(1)  # type: ignore

    fake_eiger.wait_on_arming_if_started = MagicMock(side_effect=RuntimeError())
    with pytest.raises(RuntimeError):
        fake_eiger.unstage()

    assert fake_eiger.cam.acquire.get() == 0


def test_given_not_all_frames_done_when_eiger_stopped_then_do_not_wait_for_frames_but_disarm(
    fake_eiger: EigerDetector,
):
    fake_eiger.disarm_detector = MagicMock()
    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.odin.file_writer.num_captured.sim_put(10)  # type: ignore

    fake_eiger.stop()

    fake_eiger.disarm_detector.assert_called()


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
    fake_eiger: EigerDetector,
):
    fake_eiger.odin.stop = MagicMock(return_value=NullStatus())
    fake_eiger.detector_params.use_roi_mode = True  # type: ignore
    done_status = NullStatus()

    call_func.return_value = done_status
    fake_eiger.enable_roi_mode = MagicMock(name="enable_roi_mode")
    fake_eiger.set_detector_threshold = MagicMock(name="set_detector_threshold")
    fake_eiger.set_cam_pvs = MagicMock(name="set_cam_pvs")
    fake_eiger.set_odin_number_of_frame_chunks = MagicMock(
        name="set_odin_number_of_frame_chunks"
    )
    fake_eiger.set_odin_pvs = MagicMock(name="set_odin_pvs")
    fake_eiger.set_mx_settings_pvs = MagicMock(name="set_mx_settings_pvs")
    fake_eiger.set_num_triggers_and_captures = MagicMock(
        name="set_num_triggers_and_captures"
    )
    fake_eiger._wait_for_odin_status = MagicMock(name="_wait_for_odin_status")
    fake_eiger.cam.acquire.set = MagicMock(name="set")
    fake_eiger._wait_fan_ready = MagicMock(name="_wait_fan_ready")
    fake_eiger._finish_arm = MagicMock(name="_finish_arm")

    fake_eiger.do_arming_chain()

    funcs = [
        fake_eiger.odin.stop,
        fake_eiger.enable_roi_mode,
        fake_eiger.set_detector_threshold,
        fake_eiger.set_cam_pvs,
        fake_eiger.set_odin_number_of_frame_chunks,
        fake_eiger.set_odin_pvs,
        fake_eiger.set_mx_settings_pvs,
        fake_eiger.set_num_triggers_and_captures,
        fake_eiger._wait_for_odin_status,
        fake_eiger.cam.acquire.set,
        fake_eiger._wait_fan_ready,
        fake_eiger._finish_arm,
        await_value,
    ]

    for f in funcs:
        f.assert_not_called()
        assert call(f) in call_func.mock_calls or lambda_in_calls(
            f, call_func.mock_calls
        )


@patch("ophyd.status.StatusBase.wait")
def test_stop_eiger_waits_for_status_functions_to_complete(
    mock_wait: MagicMock, fake_eiger: EigerDetector
):
    fake_eiger.stop()
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
    fake_eiger: EigerDetector,
):
    mock_await.return_value = finished_status()
    set_up_eiger_to_stage_happily(fake_eiger)

    fake_eiger.detector_params.enable_dev_shm = enable_dev_shm  # type:ignore

    fake_eiger.stage()

    assert fake_eiger.odin.fan.dev_shm_enable.get() == expected_set


def test_when_eiger_is_stopped_then_dev_shm_disabled(fake_eiger: EigerDetector):
    fake_eiger.odin.fan.dev_shm_enable.sim_put(1)  # type:ignore

    fake_eiger.stop()

    assert fake_eiger.odin.fan.dev_shm_enable.get() == 0


def test_for_other_beamlines_i03_used_as_default(params: DetectorParams):
    FakeEigerDetector: EigerDetector = make_fake_device(EigerDetector)
    fake_eiger: EigerDetector = FakeEigerDetector.with_params(
        params=params, beamline="ixx"
    )
    assert fake_eiger.beamline == "ixx"
    assert fake_eiger.timeouts == AVAILABLE_TIMEOUTS["i03"]


def test_given_eiger_is_disarming_when_eiger_is_stopped_then_wait_for_disarming_to_finish(
    fake_eiger: EigerDetector,
):
    fake_eiger.disarm_detector = MagicMock()
    fake_eiger.disarming_status = (disarming_status := MagicMock())
    disarming_status.done = False
    fake_eiger.stop()

    disarming_status.wait.assert_called_once()
    fake_eiger.disarm_detector.assert_not_called()
