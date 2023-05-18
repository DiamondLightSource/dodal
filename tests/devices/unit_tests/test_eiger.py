import threading
from unittest.mock import MagicMock, patch

import pytest
from mockito import ANY, mock, verify, when
from ophyd.sim import make_fake_device
from ophyd.status import Status
from ophyd.utils import errors

from dodal.devices.det_dim_constants import EIGER2_X_16M_SIZE
from dodal.devices.detector import DetectorParams, TriggerMode
from dodal.devices.eiger import EigerDetector
from dodal.devices.status import await_value
from dodal.devices.utils import wrap_and_do_funcs

TEST_DETECTOR_SIZE_CONSTANTS = EIGER2_X_16M_SIZE

TEST_CURRENT_ENERGY = 100.0
TEST_EXPOSURE_TIME = 1.0
TEST_DIR = "/test/dir"
TEST_PREFIX = "test"
TEST_RUN_NUMBER = 0
TEST_DETECTOR_DISTANCE = 1.0
TEST_OMEGA_START = 0.0
TEST_OMEGA_INCREMENT = 1.0
TEST_NUM_IMAGES_PER_TRIGGER = 1
TEST_NUM_TRIGGERS = 2000
TEST_USE_ROI_MODE = False
TEST_DET_DIST_TO_BEAM_CONVERTER_PATH = "tests/devices/unit_tests/test_lookup_table.txt"


def create_new_params() -> DetectorParams:
    return DetectorParams(
        TEST_CURRENT_ENERGY,
        TEST_EXPOSURE_TIME,
        TEST_DIR,
        TEST_PREFIX,
        TEST_RUN_NUMBER,
        TEST_DETECTOR_DISTANCE,
        TEST_OMEGA_START,
        TEST_OMEGA_INCREMENT,
        TEST_NUM_IMAGES_PER_TRIGGER,
        TEST_NUM_TRIGGERS,
        TEST_USE_ROI_MODE,
        TEST_DET_DIST_TO_BEAM_CONVERTER_PATH,
        detector_size_constants=TEST_DETECTOR_SIZE_CONSTANTS,
    )


@pytest.fixture
def fake_eiger():
    FakeEigerDetector: EigerDetector = make_fake_device(EigerDetector)
    fake_eiger: EigerDetector = FakeEigerDetector.with_params(
        params=create_new_params(), name="test"
    )
    return fake_eiger


@pytest.fixture
def finished_status():
    status = Status()
    status.set_finished()
    return status


@pytest.fixture
def mock_set_odin_filewriter(fake_eiger: EigerDetector):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.check_odin_initialised = MagicMock()
    fake_eiger.odin.check_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)

    def do_set(val: str):
        fake_eiger.odin.meta.file_name.sim_put(val)
        fake_eiger.odin.file_writer.id.sim_put(val)
        stat = Status()
        stat.set_finished()
        return stat

    return do_set


@pytest.mark.parametrize(
    "current_energy, request_energy, is_energy_change",
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
    current_energy: float,
    request_energy: float,
    is_energy_change: bool,
):
    status_obj = MagicMock()
    when(fake_eiger.cam.photon_energy).get().thenReturn(current_energy)
    when(fake_eiger.cam.photon_energy).set(ANY, timeout=ANY).thenReturn(status_obj)

    returned_status = fake_eiger.set_detector_threshold(request_energy)

    if is_energy_change:
        verify(fake_eiger.cam.photon_energy, times=1).set(request_energy, timeout=ANY)
        assert returned_status == status_obj
    else:
        verify(fake_eiger.cam.photon_energy, times=0).set(ANY, timeout=ANY)
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
            assert False, f"exception was raised {e}"


def test_when_set_odin_pvs_called_then_full_filename_written(fake_eiger: EigerDetector):
    expected_full_filename = f"{TEST_PREFIX}_{TEST_RUN_NUMBER}"

    status = fake_eiger.set_odin_pvs()
    status &= fake_eiger.set_odin_pvs_after_file_writer_set()

    fake_eiger.odin.file_writer.num_frames_chunks.sim_put(1)
    assert fake_eiger.detector_params is not None
    # Logic for propagating filename is not in fake eiger
    fake_eiger.odin.meta.file_name.sim_put(expected_full_filename)
    fake_eiger.odin.file_writer.id.sim_put(expected_full_filename)
    status.wait()

    assert fake_eiger.odin.file_writer.file_name.get() == expected_full_filename


def test_stage_raises_exception_if_odin_initialisation_status_not_ok(fake_eiger):
    when(fake_eiger.odin.nodes).clear_odin_errors().thenReturn(None)
    expected_error_message = "Test error"
    when(fake_eiger.odin).check_odin_initialised().thenReturn(
        (False, expected_error_message)
    )
    with pytest.raises(
        Exception, match=f"Odin not initialised: {expected_error_message}"
    ):
        fake_eiger.async_stage()


@pytest.mark.parametrize(
    "roi_mode, expected_num_change_roi_calls", [(True, 1), (False, 0)]
)
@patch("dodal.devices.eiger.await_value")
def test_stage_enables_roi_mode_correctly(
    mock_await, fake_eiger, roi_mode, expected_num_change_roi_calls
):
    when(fake_eiger.odin.nodes).clear_odin_errors().thenReturn(None)
    when(fake_eiger.odin).check_odin_initialised().thenReturn((True, ""))

    fake_eiger.detector_params.use_roi_mode = roi_mode

    fake_eiger.change_roi_mode = MagicMock()

    fake_eiger.async_stage()

    assert fake_eiger.change_roi_mode.call_count == expected_num_change_roi_calls


def test_enable_roi_mode_sets_correct_roi_mode(fake_eiger):
    mock_roi_change = MagicMock()
    fake_eiger.change_roi_mode = mock_roi_change
    fake_eiger.enable_roi_mode()
    mock_roi_change.assert_called_once_with(True)


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
        expected_detector_dimensions.height, timeout=10
    )
    mock_odin_width_set.assert_called_once_with(
        expected_detector_dimensions.width, timeout=10
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
        expected_cam_roi_mode_call, timeout=10
    )


@patch("ophyd.status.Status.__and__")
def test_unsuccessful_roi_mode_change_results_in_callback_error(mock_and, fake_eiger):
    dummy_status = Status(timeout=0)
    mock_and.return_value = dummy_status

    # Test true
    unwrapped_funcs = [
        lambda: fake_eiger.change_roi_mode(enable=True),
        lambda: fake_eiger.set_detector_threshold(
            energy=fake_eiger.detector_params.current_energy
        ),
    ]
    with pytest.raises(errors.StatusTimeoutError):
        wrap_and_do_funcs(unwrapped_funcs)

    # Test false
    with pytest.raises(errors.StatusTimeoutError):
        fake_eiger.change_roi_mode(enable=False).wait()

    # fake_eiger.log.error = MagicMock()

    # with pytest.raises(errors.StatusTimeoutError):
    #     fake_eiger.change_roi_mode(True)

    # fake_eiger.change_roi_mode(False)

    # fake_eiger.log.error.assert_called_once_with("Failed to disable ROI mode")


@patch("dodal.devices.eiger.EigerOdin.check_odin_state")
def test_bad_odin_state_results_in_unstage_returning_bad_status(
    mock_check_odin_state, fake_eiger: EigerDetector
):
    mock_check_odin_state.return_value = False
    happy_status = Status()
    happy_status.set_finished()
    fake_eiger.filewriters_finished = happy_status
    returned_status = fake_eiger.unstage()
    assert returned_status is False


def test_given_failing_odin_when_stage_then_exception_raised(fake_eiger):
    error_contents = "Got an error"
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.check_odin_initialised = MagicMock()
    fake_eiger.odin.check_odin_initialised.return_value = (False, error_contents)
    with pytest.raises(Exception) as e:
        fake_eiger.async_stage()
        assert error_contents in e.value


@patch("dodal.devices.eiger.await_value")
def test_stage_runs_successfully(mock_await, fake_eiger: EigerDetector):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.check_odin_initialised = MagicMock()
    fake_eiger.odin.check_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)
    fake_eiger.async_stage()


@patch("dodal.devices.eiger.await_value")
def test_given_stale_parameters_goes_high_before_callbacks_then_stale_parameters_waited_on(
    mock_await,
    fake_eiger: EigerDetector,
):
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.check_odin_initialised = MagicMock()
    fake_eiger.odin.check_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)

    def wait_on_staging():
        fake_eiger.async_stage()

    waiting_status = Status()
    fake_eiger.cam.num_images.set = MagicMock(return_value=waiting_status)

    thread = threading.Thread(target=wait_on_staging, daemon=True)
    thread.start()

    assert thread.is_alive()

    fake_eiger.stale_params.sim_put(1)
    waiting_status.set_finished()

    assert thread.is_alive()

    fake_eiger.stale_params.sim_put(0)

    thread.join(0.2)
    assert not thread.is_alive()


# Tests transition from waiting for stale params to _wait_for_odin_status()
def test_when_stage_called_then_odin_started_after_stale_params_goes_low(
    fake_eiger: EigerDetector, mock_set_odin_filewriter, finished_status
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    fake_eiger.stale_params.sim_put(1)
    fake_eiger.odin.file_writer.capture.sim_put(0)

    fake_eiger.arming_status = MagicMock()

    fake_eiger.async_stage()

    assert fake_eiger.odin.file_writer.capture.get() == 0

    fake_eiger.stale_params.sim_put(0)

    await_value(fake_eiger.odin.file_writer.capture, 1).wait(1)


# Tests transition from _wait_for_odin_status to _wait_for_cam_acquire
def test_when_stage_called_then_cam_acquired_on_meta_ready(
    fake_eiger: EigerDetector, mock_set_odin_filewriter, finished_status
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    fake_eiger.odin.file_writer.capture.sim_put(0)
    fake_eiger.stale_params.sim_put(0)
    fake_eiger.arming_status = MagicMock()
    fake_eiger.async_stage()

    assert fake_eiger.cam.acquire.get() == 0

    fake_eiger.odin.meta.ready.sim_put(1)

    await_value(fake_eiger.cam.acquire, 1).wait(1)


# Tests transition from _wait_fan_ready to _finish_arm
def test_when_stage_called_then_finish_arm_on_fan_ready(
    fake_eiger: EigerDetector, mock_set_odin_filewriter, finished_status
):
    fake_eiger.odin.file_writer.file_name.set = MagicMock(
        side_effect=mock_set_odin_filewriter
    )

    # Mock this function so arming actually finishes
    fake_eiger.odin.create_finished_status = MagicMock()

    fake_eiger.odin.fan.ready.sim_put(1)
    fake_eiger.odin.file_writer.capture.sim_put(0)
    fake_eiger.arming_status = MagicMock()

    unwrapped_funcs = [fake_eiger._wait_fan_ready, fake_eiger._finish_arm]
    status = wrap_and_do_funcs(unwrapped_funcs)

    fake_eiger.odin.meta.ready.sim_put(1)
    status.wait(5)


def test_arming_not_called_when_already_armed(fake_eiger: EigerDetector):
    finished = MagicMock()

    def finish_arm():
        if not fake_eiger.armed:
            fake_eiger._finish_arm()
            finished()

    fake_eiger.armed = False
    fake_eiger.make_chained_functions = MagicMock(side_effect=finish_arm)
    fake_eiger.async_stage = MagicMock(side_effect=fake_eiger.make_chained_functions)
    fake_eiger.async_stage()
    fake_eiger.async_stage()
    finished.assert_called_once()


def test_disarming_not_called_when_already_armed(
    fake_eiger: EigerDetector, mock_set_odin_filewriter, finished_status
):
    fake_eiger.disarm_detector = MagicMock()
    fake_eiger.filewriters_finished = finished_status
    fake_eiger.unstage()
    fake_eiger.disarm_detector.assert_not_called()


# @patch("dodal.devices.eiger.await_value")
# @patch("ophyd.status.Status.__and__")
# @pytest.mark.parametrize(
#     "func",
#     [
#         ("fake_eiger.set_detector_threshold(finished_status, 200.0)"),
#         ("fake_eiger.set_cam_pvs(finished_status)"),
#         ("fake_eiger.set_odin_pvs(finished_status)"),
#         ("fake_eiger.set_odin_pvs_after_file_writer_set(finished_status)"),
#         ("fake_eiger.set_mx_settings_pvs(finished_status)"),
#         ("fake_eiger.set_num_triggers_and_captures(finished_status)"),
#         ("fake_eiger.wait_for_odin_status(finished_status)"),
#         ("fake_eiger.wait_for_cam_acquire(finished_status)"),
#         ("fake_eiger.wait_fan_ready(finished_status)"),
#         ("fake_eiger.wait_for_stale_parameters()"),
#     ],
# )
# def test_check_callback_error(
#     mock_and, mock_await, fake_eiger: EigerDetector, func, finished_status
# ):
#     fake_eiger.odin.file_writer.num_frames_chunks.set = MagicMock()
#     fake_eiger.odin.file_writer.num_frames_chunks.set.return_value = Status(timeout=0)
#     fake_eiger.cam.acquire.set = MagicMock()
#     fake_eiger.cam.acquire.set.return_value = Status(timeout=0)
#     dummy_status = Status(timeout=0)
#     mock_and.return_value = dummy_status
#     fake_eiger.cam.photon_energy.set = MagicMock()
#     fake_eiger.cam.photon_energy.set.return_value = dummy_status
#     fake_eiger.stale_params.sim_put(1)
#     mock_await.return_value = Status(timeout=0)
#     with pytest.raises(errors.StatusTimeoutError):
#         eval(func)


def test_given_in_free_run_mode_when_staged_then_triggers_and_filewriter_set_correctly(
    fake_eiger: EigerDetector, finished_status
):
    fake_eiger.filewriters_finished = finished_status
    fake_eiger.odin.nodes.clear_odin_errors = MagicMock()
    fake_eiger.odin.check_odin_initialised = MagicMock()
    fake_eiger.odin.check_odin_initialised.return_value = (True, "")
    fake_eiger.odin.file_writer.file_path.put(True)
    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.set_num_triggers_and_captures()
    assert fake_eiger.cam.num_triggers.get() > fake_eiger.detector_params.num_triggers
    assert fake_eiger.odin.file_writer.num_capture.get() == 0


def test_given_in_free_run_mode_when_unstaged_then_waiting_on_file_writer_to_finish_correctly(
    fake_eiger: EigerDetector, finished_status
):
    fake_eiger.filewriters_finished = finished_status

    fake_eiger.odin.file_writer.capture.sim_put(1)
    fake_eiger.odin.file_writer.num_captured.sim_put(2000)
    fake_eiger.odin.check_odin_state = MagicMock(return_value=True)

    fake_eiger.detector_params.trigger_mode = TriggerMode.FREE_RUN
    fake_eiger.armed = True
    fake_eiger.unstage()

    assert fake_eiger.odin.meta.stop_writing.get() == 1
    assert fake_eiger.odin.file_writer.capture.get() == 0
