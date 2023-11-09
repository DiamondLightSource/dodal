import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.run_engine import RunEngine
from mockito import mock, verify, when
from mockito.matchers import ANY, ARGS, KWARGS
from ophyd.sim import make_fake_device

from dodal.devices.fast_grid_scan import (
    FastGridScan,
    GridScanParams,
    set_fast_grid_scan_params,
)
from dodal.devices.smargon import Smargon


@pytest.fixture
def fast_grid_scan():
    FakeFastGridScan = make_fake_device(FastGridScan)
    fast_grid_scan: FastGridScan = FakeFastGridScan(name="test fake FGS")
    fast_grid_scan.scan_invalid.pvname = ""

    yield fast_grid_scan


def test_given_settings_valid_when_kickoff_then_run_started(
    fast_grid_scan: FastGridScan,
):
    when(fast_grid_scan.scan_invalid).get().thenReturn(False)
    when(fast_grid_scan.position_counter).get().thenReturn(0)

    mock_run_set_status = mock()
    when(fast_grid_scan.run_cmd).put(ANY).thenReturn(mock_run_set_status)
    fast_grid_scan.status.subscribe = lambda func, **_: func(1)

    status = fast_grid_scan.kickoff()

    status.wait()
    assert status.exception() is None

    verify(fast_grid_scan.run_cmd).put(1)


def run_test_on_complete_watcher(
    fast_grid_scan: FastGridScan, num_pos_1d, put_value, expected_frac
):
    RE = RunEngine()
    RE(
        set_fast_grid_scan_params(
            fast_grid_scan, GridScanParams(x_steps=num_pos_1d, y_steps=num_pos_1d)
        )
    )

    complete_status = fast_grid_scan.complete()
    watcher = mock()
    complete_status.watch(watcher)

    fast_grid_scan.position_counter.sim_put(put_value)
    verify(watcher).__call__(
        *ARGS,
        current=put_value,
        target=num_pos_1d**2,
        fraction=expected_frac,
        **KWARGS,
    )
    return complete_status


def test_when_new_image_then_complete_watcher_notified(fast_grid_scan: FastGridScan):
    run_test_on_complete_watcher(fast_grid_scan, 2, 1, 3 / 4)


def test_given_0_expected_images_then_complete_watcher_correct(
    fast_grid_scan: FastGridScan,
):
    run_test_on_complete_watcher(fast_grid_scan, 0, 1, 0)


@pytest.mark.parametrize(
    "steps, expected_images",
    [
        ((10, 10, 0), 100),
        ((30, 5, 10), 450),
        ((7, 0, 5), 35),
    ],
)
def test_given_different_step_numbers_then_expected_images_correct(
    fast_grid_scan: FastGridScan, steps, expected_images
):
    fast_grid_scan.x_steps.sim_put(steps[0])
    fast_grid_scan.y_steps.sim_put(steps[1])
    fast_grid_scan.z_steps.sim_put(steps[2])

    assert fast_grid_scan.expected_images.get() == expected_images


def test_given_invalid_image_number_then_complete_watcher_correct(
    fast_grid_scan: FastGridScan,
):
    complete_status = run_test_on_complete_watcher(fast_grid_scan, 1, "BAD", None)
    assert complete_status.exception()


def test_running_finished_with_all_images_done_then_complete_status_finishes_not_in_error(
    fast_grid_scan: FastGridScan,
):
    num_pos_1d = 2
    RE = RunEngine()
    RE(
        set_fast_grid_scan_params(
            fast_grid_scan, GridScanParams(x_steps=num_pos_1d, y_steps=num_pos_1d)
        )
    )

    fast_grid_scan.status.sim_put(1)

    complete_status = fast_grid_scan.complete()
    assert not complete_status.done
    fast_grid_scan.position_counter.sim_put(num_pos_1d**2)
    fast_grid_scan.status.sim_put(0)

    complete_status.wait()

    assert complete_status.done
    assert complete_status.exception() is None


def create_motor_bundle_with_limits(low_limit, high_limit) -> Smargon:
    FakeSmargon = make_fake_device(Smargon)
    grid_scan_motor_bundle: Smargon = FakeSmargon(name="test fake Smargon")
    grid_scan_motor_bundle.wait_for_connection()
    for axis in [
        grid_scan_motor_bundle.x,
        grid_scan_motor_bundle.y,
        grid_scan_motor_bundle.z,
    ]:
        axis.low_limit_travel.sim_put(low_limit)
        axis.high_limit_travel.sim_put(high_limit)
    return grid_scan_motor_bundle


@pytest.mark.parametrize(
    "position, expected_in_limit",
    [
        (-1, False),
        (20, False),
        (5, True),
    ],
)
def test_within_limits_check(position, expected_in_limit):
    limits = create_motor_bundle_with_limits(0.0, 10).get_xyz_limits()
    assert limits.x.is_within(position) == expected_in_limit


PASSING_LINE_1 = (1, 5, 1)
PASSING_LINE_2 = (0, 10, 0.5)
FAILING_LINE_1 = (-1, 20, 0.5)
PASSING_CONST = 6
FAILING_CONST = 15


@pytest.mark.parametrize(
    "start, steps, size, expected_in_limits",
    [
        (*PASSING_LINE_1, True),
        (*PASSING_LINE_2, True),
        (*FAILING_LINE_1, False),
        (-1, 5, 1, False),
        (-1, 10, 2, False),
        (0, 10, 0.1, True),
        (5, 10, 0.5, True),
        (5, 20, 0.6, False),
    ],
)
def test_scan_within_limits_1d(start, steps, size, expected_in_limits):
    motor_bundle = create_motor_bundle_with_limits(0.0, 10.0)
    grid_params = GridScanParams(x_start=start, x_steps=steps, x_step_size=size)
    assert grid_params.is_valid(motor_bundle.get_xyz_limits()) == expected_in_limits


@pytest.mark.parametrize(
    "x_start, x_steps, x_size, y1_start, y_steps, y_size, z1_start, expected_in_limits",
    [
        (*PASSING_LINE_1, *PASSING_LINE_2, PASSING_CONST, True),
        (*PASSING_LINE_1, *FAILING_LINE_1, PASSING_CONST, False),
        (*PASSING_LINE_1, *PASSING_LINE_2, FAILING_CONST, False),
    ],
)
def test_scan_within_limits_2d(
    x_start, x_steps, x_size, y1_start, y_steps, y_size, z1_start, expected_in_limits
):
    motor_bundle = create_motor_bundle_with_limits(0.0, 10.0)
    grid_params = GridScanParams(
        x_start=x_start,
        x_steps=x_steps,
        x_step_size=x_size,
        y1_start=y1_start,
        y_steps=y_steps,
        y_step_size=y_size,
        z1_start=z1_start,
    )
    assert grid_params.is_valid(motor_bundle.get_xyz_limits()) == expected_in_limits


@pytest.mark.parametrize(
    "x_start, x_steps, x_size, y1_start, y_steps, y_size, z1_start, z2_start, z_steps, z_size, y2_start, expected_in_limits",
    [
        (
            *PASSING_LINE_1,
            *PASSING_LINE_2,
            PASSING_CONST,
            *PASSING_LINE_1,
            PASSING_CONST,
            True,
        ),
        (
            *PASSING_LINE_1,
            *PASSING_LINE_2,
            PASSING_CONST,
            *PASSING_LINE_1,
            FAILING_CONST,
            False,
        ),
        (
            *PASSING_LINE_1,
            *PASSING_LINE_2,
            PASSING_CONST,
            *FAILING_LINE_1,
            PASSING_CONST,
            False,
        ),
    ],
)
def test_scan_within_limits_3d(
    x_start,
    x_steps,
    x_size,
    y1_start,
    y_steps,
    y_size,
    z1_start,
    z2_start,
    z_steps,
    z_size,
    y2_start,
    expected_in_limits,
):
    motor_bundle = create_motor_bundle_with_limits(0.0, 10.0)
    grid_params = GridScanParams(
        x_start=x_start,
        x_steps=x_steps,
        x_step_size=x_size,
        y1_start=y1_start,
        y_steps=y_steps,
        y_step_size=y_size,
        z1_start=z1_start,
        z2_start=z2_start,
        z_steps=z_steps,
        z_step_size=z_size,
        y2_start=y2_start,
    )
    assert grid_params.is_valid(motor_bundle.get_xyz_limits()) == expected_in_limits


@pytest.fixture
def grid_scan_params():
    yield GridScanParams(
        x_steps=10,
        y_steps=15,
        z_steps=20,
        x_step_size=0.3,
        y_step_size=0.2,
        z_step_size=0.1,
        x_start=0,
        y1_start=1,
        y2_start=2,
        z1_start=3,
        z2_start=4,
    )


@pytest.mark.parametrize(
    "grid_position",
    [
        (np.array([-1, 2, 4])),
        (np.array([11, 2, 4])),
        (np.array([1, 17, 4])),
        (np.array([1, 5, 22])),
    ],
)
def test_given_x_y_z_out_of_range_then_converting_to_motor_coords_raises(
    grid_scan_params: GridScanParams, grid_position
):
    with pytest.raises(IndexError):
        grid_scan_params.grid_position_to_motor_position(grid_position)


def test_given_x_y_z_of_origin_when_get_motor_positions_then_initial_positions_returned(
    grid_scan_params: GridScanParams,
):
    motor_positions = grid_scan_params.grid_position_to_motor_position(
        np.array([0, 0, 0])
    )
    assert np.allclose(motor_positions, np.array([0, 1, 4]))


@pytest.mark.parametrize(
    "grid_position, expected_x, expected_y, expected_z",
    [
        (np.array([1, 1, 1]), 0.3, 1.2, 4.1),
        (np.array([2, 11, 16]), 0.6, 3.2, 5.6),
        (np.array([6, 5, 5]), 1.8, 2.0, 4.5),
    ],
)
def test_given_various_x_y_z_when_get_motor_positions_then_expected_positions_returned(
    grid_scan_params: GridScanParams, grid_position, expected_x, expected_y, expected_z
):
    motor_positions = grid_scan_params.grid_position_to_motor_position(grid_position)
    np.testing.assert_allclose(
        motor_positions, np.array([expected_x, expected_y, expected_z])
    )


def test_can_run_fast_grid_scan_in_run_engine(fast_grid_scan):
    @bpp.run_decorator()
    def kickoff_and_complete(device):
        yield from bps.kickoff(device)
        yield from bps.complete(device)

    RE = RunEngine()
    RE(kickoff_and_complete(fast_grid_scan))
    assert RE.state == "idle"


def test_given_x_y_z_steps_when_full_number_calculated_then_answer_is_as_expected(
    grid_scan_params: GridScanParams,
):
    assert grid_scan_params.get_num_images() == 350


@pytest.mark.parametrize(
    "test_dwell_times, expected_dwell_time_is_integer",
    [
        (9000, True),
        (1000, True),
        (100.1, True),
        (100.09, True),
        (150.7, False),
        (10, True),
        (99, True),
        (59, True),
        (0.4, False),
        (0.9, False),
        (0.44, False),
        (0.99, False),
        (0.01, False),
        (0.09, False),
        (0.001, False),
        (0.009, False),
    ],
)
def test_non_test_integer_dwell_time(test_dwell_times, expected_dwell_time_is_integer):
    if expected_dwell_time_is_integer:
        params = GridScanParams(dwell_time_ms=test_dwell_times)
        assert params.dwell_time_ms == test_dwell_times
    else:
        with pytest.raises(ValueError):
            GridScanParams(dwell_time_ms=test_dwell_times)
