from collections.abc import Mapping, Sequence

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import StandardDetector
from ophyd_async.testing import assert_emitted
from pydantic import ValidationError

from dodal.devices.motors import Motor
from dodal.plans.scans.step_scans import (
    _group_args_by_movable,
    _make_step_scan_args,
    _make_stepped_list_num,
    _make_stepped_list_step,
    _round_list_elements,
    step_grid_rscan,
    step_grid_scan,
    step_rscan,
    step_scan,
)


def _assert_emitted(
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    num: int,
    start: int = 1,
    descriptor: int = 1,
    stream_resource: int = 2,
    stop: int = 1,
) -> None:
    numbers = {
        "start": start,
        "descriptor": descriptor,
        "event": num,
        "stop": stop,
    }
    # If detector, add stream parts.
    if len(detectors) > 0:
        # Order matters
        numbers = {
            "start": start,
            "descriptor": descriptor,
            "stream_resource": stream_resource,
            "stream_datum": num * stream_resource,
            "event": num,
            "stop": stop,
        }
    assert_emitted(run_engine_documents, **numbers)


@pytest.mark.parametrize(
    "stepped_list, params, rounded_element",
    (
        [[0.1234, 1.1234, 2.1234], [0.123, 2.123, 1], 0.123],
        [[0.1234, 1.1234, 2.1234], [0.12, 2.12, 1], 0.12],
        [[0.1234, 1.1234, 2.1234], [0.1, 2.1, 1], 0.1],
        [[0.1234, 1.1234, 2.1234], [0, 2, 1], 0],
    ),
)
def test_round_list_elements(
    stepped_list: list[float], params: list[float], rounded_element: float
):
    rounded_list = _round_list_elements(stepped_list, params)
    assert rounded_list[0] == rounded_element


@pytest.mark.parametrize(
    "start, stop, step",
    (
        [-1, 1, 0.1],
        [-2, 2, 0.2],
        [1, -1, -0.1],
        [2, -2, -0.2],
        [1, -1, 0.1],
        [2, -2, 0.2],
    ),
)
def test_make_stepped_list_step(start: float, stop: float, step: float):
    stepped_list = _make_stepped_list_step(start, stop, step)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_step_with_large_step():
    stepped_list = _make_stepped_list_step(0, 1, 5)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 2
    assert stepped_list[0] == 0
    assert stepped_list[-1] == 1


@pytest.mark.parametrize("start, step", ([-1, 0.1], [-2, 0.2], [1, -0.1], [2, -0.2]))
def test_make_stepped_list_num(start: float, step: float):
    stepped_list = _make_stepped_list_num(start, step, num=21)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_fails_when_given_equal_start_and_stop_values():
    with pytest.raises(ValueError):
        _make_stepped_list_step(start=1.1, stop=1.1, step=0.25)


@pytest.mark.parametrize(
    "x_list, y_list, grid, final_shape, final_length",
    (
        [[0, 1, 0.25], [0, 0.1], False, [5], 4],
        [[0, 1, 0.25], [0, 1, 0.2], True, [5, 6], 4],
        [[0, -1, -0.25], [0, -0.1], False, [5], 4],
        [[0, -1, -0.25], [0, -1, -0.2], True, [5, 6], 4],
    ),
)
def test_make_step_scan_args(
    x_axis: Motor,
    x_list: list[float],
    y_axis: Motor,
    y_list: list[float],
    grid: bool,
    final_shape: list,
    final_length: int,
):
    args, shape = _make_step_scan_args(
        args=[x_axis, *x_list, y_axis, *y_list], grid=grid
    )
    assert shape == final_shape
    assert len(args) == final_length
    assert args[0] == x_axis
    assert args[2] == y_axis


@pytest.mark.parametrize(
    "x_list, y_list, z_list, grid",
    (
        [[0, 1], [0, 0.2], [0, 0.5], False],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.2, 0.5], False],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.5], True],
        [[0, 1, 0.25], [0, 1, 0.2], [0, 0.5], True],
    ),
)
def test_make_step_scan_args_fails_when_given_incorrect_number_of_parameters(
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    z_axis: Motor,
    z_list: list,
    grid: bool,
):
    with pytest.raises(ValueError):
        _make_step_scan_args(
            args=[x_axis, *x_list, y_axis, *y_list, z_axis, *z_list], grid=grid
        )


def test_group_args_by_movable(x_axis: Motor, y_axis: Motor, z_axis: Motor):
    groups = _group_args_by_movable([x_axis, 0, 10, 1, y_axis, 5, 0.5, z_axis])
    assert groups == [(x_axis, [0, 10, 1]), (y_axis, [5, 0.5]), (z_axis, [])]


def test_group_args_by_movable_fails_when_given_no_args():
    with pytest.raises(ValueError, match="No movables provided"):
        _group_args_by_movable([])


def test_group_args_by_movable_fails_when_first_arg_is_not_movable(x_axis: Motor):
    with pytest.raises(ValueError, match="Expected a movable"):
        _group_args_by_movable([0, x_axis, 10, 1])


def test_make_step_scan_args_concurrent_positions(x_axis: Motor, y_axis: Motor):
    args, shape = _make_step_scan_args([x_axis, 0, 2, 1, y_axis, 5, 0.5], grid=False)
    assert args == [x_axis, [0, 1, 2], y_axis, [5, 5.5, 6]]
    assert shape == [3]


def test_make_step_scan_args_grid_positions(x_axis: Motor, y_axis: Motor):
    args, shape = _make_step_scan_args([x_axis, 0, 2, 1, y_axis, 0, 1, 0.5], grid=True)
    assert args == [x_axis, [0, 1, 2], y_axis, [0, 0.5, 1]]
    assert shape == [3, 3]


def test_step_scan_fails_when_given_non_numeric_parameter(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor
):
    with pytest.raises(ValidationError):
        run_engine(step_scan([det], x_axis, 0, "ten", 1))  # type: ignore


@pytest.mark.parametrize(
    "plan, args, expected_shape",
    (
        [step_scan, [0, 1, 0.5], [3]],
        [step_rscan, [0, 1, 0.5], [3]],
        [step_grid_scan, [0, 1, 0.5, "y", 0, 1, 0.25], [3, 5]],
        [step_grid_rscan, [0, 1, 0.5, "y", 0, 1, 0.25], [3, 5]],
    ),
)
def test_step_scans_add_shape_and_metadata_to_start_document(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    x_axis: Motor,
    y_axis: Motor,
    plan,
    args: list,
    expected_shape: list[int],
):
    metadata = {"sample": "test"}
    args = [y_axis if a == "y" else a for a in args]
    run_engine(plan([], x_axis, *args, metadata=metadata))
    start = run_engine_documents["start"][0]
    assert start["shape"] == expected_shape
    assert start["sample"] == "test"
    assert metadata == {"sample": "test"}


@pytest.fixture(params=[0, 1], ids=["0 detector(s)", "1 detector(s)"])
def detectors(
    request: pytest.FixtureRequest, det: StandardDetector
) -> Sequence[StandardDetector]:
    return [] if request.param == 0 else [det]


@pytest.mark.parametrize(
    "x_list, num", ([[0, 1, 0.1], 11], [[-1, 1, 0.1], 21], [[0, 10, 1], 11])
)
def test_step_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    num,
):
    run_engine(step_scan(detectors, x_axis, *x_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 0.1], 5],
        [[-1, 1, 0.25], [-1, 0.1], 9],
        [[0, 10, 2.5], [0, 1], 5],
    ),
)
def test_step_scan_with_multiple_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(step_scan(detectors, x_axis, *x_list, y_axis, *y_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 2, 0.5], 25],
        [[-1, 1, 0.25], [1, -1, -0.5], 45],
        [[0, 10, 2.5], [0, -10, -2.5], 25],
    ),
)
def test_step_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(step_grid_scan(detectors, x_axis, *x_list, y_axis, *y_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 2, 0.5], 25],
        [[-1, 1, 0.25], [1, -1, -0.5], 45],
    ),
)
def test_step_grid_scan_when_not_snaking(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(
        step_grid_scan(
            detectors,
            x_axis,
            *x_list,
            y_axis,
            *y_list,
            snake_axes=False,
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_scan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    with pytest.raises(ValueError):
        run_engine(step_grid_scan(detectors, x_axis, *x_list, y_axis, *y_list))


@pytest.mark.parametrize(
    "x_list, num", ([[0, 1, 0.1], 11], [[-1, 1, 0.1], 21], [[0, 10, 1], 11])
)
def test_step_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    num,
):
    run_engine(step_rscan(detectors, x_axis, *x_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 0.1], 5],
        [[-1, 1, 0.25], [-1, 0.1], 9],
        [[0, 10, 2.5], [0, 1], 5],
    ),
)
def test_step_rscan_with_multiple_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(step_rscan(detectors, x_axis, *x_list, y_axis, *y_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 2, 0.5], 25],
        [[-1, 1, 0.25], [1, -1, -0.5], 45],
        [[0, 10, 2.5], [0, -10, -2.5], 25],
    ),
)
def test_step_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(step_grid_rscan(detectors, x_axis, *x_list, y_axis, *y_list))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 2, 0.5], 25],
        [[-1, 1, 0.25], [1, -1, -0.5], 45],
    ),
)
def test_step_grid_rscan_when_not_snaking(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    num,
):
    run_engine(
        step_grid_rscan(
            detectors,
            x_axis,
            *x_list,
            y_axis,
            *y_list,
            snake_axes=False,
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize(
    "x_list, y_list", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_rscan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    with pytest.raises(ValueError):
        run_engine(step_grid_rscan(detectors, x_axis, *x_list, y_axis, *y_list))
