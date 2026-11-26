from collections.abc import Mapping, Sequence
from typing import Any

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import StandardDetector
from ophyd_async.testing import assert_emitted

from dodal.devices.motors import Motor
from dodal.plans.scans.step_scans import (
    _decimal_places,
    _group_args_by_movable,
    _make_step_scan_args,
    _make_step_scan_md,
    _make_stepped_list_num,
    _make_stepped_list_step,
    step_grid_rscan,
    step_grid_scan,
    step_rscan,
    step_scan,
)

CONCURRENT_PLANS = [step_scan, step_rscan]
GRID_PLANS = [step_grid_scan, step_grid_rscan]
ALL_PLANS = CONCURRENT_PLANS + GRID_PLANS

# Placeholders for the x_axis and y_axis fixtures in parametrized args.
X = object()
Y = object()


@pytest.fixture
def resolve(x_axis: Motor, y_axis: Motor):
    """Replace the X and Y placeholders in a list with the x_axis and y_axis."""

    def _resolve(values: list[Any]) -> list[Any]:
        return [x_axis if v is X else y_axis if v is Y else v for v in values]

    return _resolve


@pytest.fixture(params=[0, 1], ids=["0 detector(s)", "1 detector(s)"])
def detectors(
    request: pytest.FixtureRequest, det: StandardDetector
) -> Sequence[StandardDetector]:
    return [det] * request.param


def _assert_emitted(
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    num: int,
) -> None:
    if detectors:
        # The sim detector writes 2 streams, each needing a stream_datum per point.
        assert_emitted(
            run_engine_documents,
            start=1,
            descriptor=1,
            stream_resource=2,
            stream_datum=2 * num,
            event=num,
            stop=1,
        )
    else:
        assert_emitted(run_engine_documents, start=1, descriptor=1, event=num, stop=1)


@pytest.mark.parametrize(
    "values, decimal_places",
    [([1, 0.5, 0.25], 2), ([0, 2, 1], 0), ([-0.1], 1), ([1e-5], 5)],
)
def test_decimal_places(values: list[float], decimal_places: int):
    assert _decimal_places(*values) == decimal_places


@pytest.mark.parametrize(
    "start, stop, step, expected",
    [
        pytest.param(0, 1, 0.25, [0, 0.25, 0.5, 0.75, 1], id="forwards"),
        pytest.param(1, 0, 0.25, [1, 0.75, 0.5, 0.25, 0], id="backwards"),
        pytest.param(1, 0, -0.25, [1, 0.75, 0.5, 0.25, 0], id="step sign ignored"),
        pytest.param(
            -1, 1, 0.1, [round(-1 + 0.1 * i, 1) for i in range(21)], id="through 0"
        ),
        pytest.param(0, 0.3, 0.1, [0, 0.1, 0.2, 0.3], id="float error rounded"),
        pytest.param(0, 1, 0.3, [0, 0.3, 0.6, 0.9], id="stop not reached"),
        pytest.param(0, 0.99, 0.25, [0, 0.25, 0.5, 0.75, 1], id="within tolerance"),
        pytest.param(0, 1.95, 1, [0, 1, 2], id="tolerance is inclusive"),
        pytest.param(0, 1, 5, [0, 1], id="step larger than range"),
        pytest.param(0.1, 0.3, 5, [0.1, 0.3], id="step larger than range rounded"),
    ],
)
def test_make_stepped_list_step(
    start: float, stop: float, step: float, expected: list[float]
):
    assert _make_stepped_list_step(start, stop, step) == expected


@pytest.mark.parametrize(
    "start, stop, step, match",
    [(1.1, 1.1, 0.25, "cannot be the same"), (0, 1, 0, "Step cannot be zero")],
)
def test_make_stepped_list_step_fails_with_invalid_params(
    start: float, stop: float, step: float, match: str
):
    with pytest.raises(ValueError, match=match):
        _make_stepped_list_step(start, stop, step)


@pytest.mark.parametrize(
    "start, step, num, expected",
    [(5, 0.5, 3, [5, 5.5, 6]), (1, -0.1, 3, [1, 0.9, 0.8]), (2, 0, 3, [2, 2, 2])],
)
def test_make_stepped_list_num(
    start: float, step: float, num: int, expected: list[float]
):
    assert _make_stepped_list_num(start, step, num) == expected


def test_group_args_by_movable(x_axis: Motor, y_axis: Motor, z_axis: Motor):
    groups = _group_args_by_movable([x_axis, 0, 10, 1, y_axis, 5, 0.5, z_axis])
    assert groups == [(x_axis, [0, 10, 1]), (y_axis, [5, 0.5]), (z_axis, [])]


@pytest.mark.parametrize(
    "args, error, match",
    [
        ([], ValueError, "No movables provided"),
        ([0, X, 10, 1], ValueError, "Expected a movable as the first argument"),
        ([X, 0, "ten", 1], TypeError, "Expected a movable or a number, got 'ten'"),
    ],
)
def test_group_args_by_movable_fails_with_invalid_args(
    resolve, args: list, error: type[Exception], match: str
):
    with pytest.raises(error, match=match):
        _group_args_by_movable(resolve(args))


@pytest.mark.parametrize(
    "args, grid, expected_args, expected_shape",
    [
        ([X, 0, 2, 1, Y, 5, 0.5], False, [X, [0, 1, 2], Y, [5, 5.5, 6]], [3]),
        (
            [X, 0, -1, 0.5, Y, 0, -0.1],
            False,
            [X, [0, -0.5, -1], Y, [0, -0.1, -0.2]],
            [3],
        ),
        ([X, 0, 2, 1, Y, 0, 1, 0.5], True, [X, [0, 1, 2], Y, [0, 0.5, 1]], [3, 3]),
    ],
)
def test_make_step_scan_args(
    resolve, args: list, grid: bool, expected_args: list, expected_shape: list[int]
):
    assert _make_step_scan_args(resolve(args), grid=grid) == (
        resolve(expected_args),
        expected_shape,
    )


@pytest.mark.parametrize(
    "args, grid, match",
    [
        ([X, 0, 1], False, "2 parameters for x_axis, rather than 3"),
        ([X, 0, 1, 0.5, Y, 0, 1, 0.5], False, "3 parameters for y_axis, rather than 2"),
        ([X, 0, 1, 0.5, Y, 0, 0.5], True, "2 parameters for y_axis, rather than 3"),
        ([X, 0, 1, 0.5, Y, 0, 1, 0.5, 1], True, "4 parameters for y_axis"),
    ],
)
def test_make_step_scan_args_fails_with_wrong_number_of_params(
    resolve, args: list, grid: bool, match: str
):
    with pytest.raises(ValueError, match=match):
        _make_step_scan_args(resolve(args), grid=grid)


def test_make_step_scan_md(det: StandardDetector, x_axis: Motor, y_axis: Motor):
    md = _make_step_scan_md(
        "step_grid_scan",
        [det],
        [x_axis, 0, 1, 0.5, y_axis, 0, 2, 1],
        [3, 3],
        None,
        snake_axes=True,
    )
    assert md == {
        "plan_name": "step_grid_scan",
        "plan_args": {
            "detectors": [repr(det)],
            "args": [repr(x_axis), 0, 1, 0.5, repr(y_axis), 0, 2, 1],
            "snake_axes": True,
        },
        "detectors": [det.name],
        "shape": [3, 3],
    }


def test_make_step_scan_md_user_metadata_takes_priority(
    det: StandardDetector, x_axis: Motor
):
    metadata = {"plan_name": "custom", "detectors": ["custom"], "sample": "test"}
    md = _make_step_scan_md("step_scan", [det], [x_axis, 0, 1, 0.5], [3], metadata)
    assert md["plan_name"] == "custom"
    assert md["detectors"] == ["custom"]
    assert md["sample"] == "test"
    assert md["shape"] == [3]


@pytest.mark.parametrize("plan", CONCURRENT_PLANS)
@pytest.mark.parametrize(
    "args, num",
    [
        ([X, 0, 1, 0.1], 11),
        ([X, -1, 1, 0.1], 21),
        ([X, 0, 1, 0.25, Y, 0, 0.1], 5),
        ([X, -1, 1, 0.25, Y, -1, 0.1], 9),
    ],
)
def test_concurrent_step_scans(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    resolve,
    plan,
    args: list,
    num: int,
):
    run_engine(plan(detectors, *resolve(args)))
    _assert_emitted(run_engine_documents, detectors, num)


@pytest.mark.parametrize("plan", GRID_PLANS)
@pytest.mark.parametrize("snake_axes", [True, False])
@pytest.mark.parametrize(
    "args, num",
    [([X, 0, 1, 0.25, Y, 0, 2, 0.5], 25), ([X, -1, 1, 0.25, Y, 1, -1, -0.5], 45)],
)
def test_grid_step_scans(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    resolve,
    plan,
    snake_axes: bool,
    args: list,
    num: int,
):
    run_engine(plan(detectors, *resolve(args), snake_axes=snake_axes))
    _assert_emitted(run_engine_documents, detectors, num)
    assert run_engine_documents["start"][0]["plan_args"]["snake_axes"] is snake_axes


@pytest.mark.parametrize("plan", ALL_PLANS)
def test_step_scans_write_start_metadata(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    plan,
):
    grid = plan in GRID_PLANS
    y_args = [0, 1, 0.25] if grid else [0, 0.25]
    metadata = {"sample": "test"}

    run_engine(plan([det], x_axis, 0, 1, 0.5, y_axis, *y_args, metadata=metadata))

    start = run_engine_documents["start"][0]
    assert start["plan_name"] == plan.__name__
    assert start["plan_args"] == {
        "detectors": [repr(det)],
        "args": [repr(x_axis), 0, 1, 0.5, repr(y_axis), *y_args],
        **({"snake_axes": True} if grid else {}),
    }
    assert start["shape"] == ([3, 5] if grid else [3])
    assert start["detectors"] == [det.name]
    assert list(start["motors"]) == [x_axis.name, y_axis.name]
    assert start["sample"] == "test"
    assert metadata == {"sample": "test"}


@pytest.mark.parametrize("plan", ALL_PLANS)
def test_step_scans_fail_with_invalid_args(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, plan
):
    with pytest.raises(TypeError, match="Expected a movable or a number"):
        run_engine(plan([det], x_axis, 0, "ten", 1))


@pytest.mark.parametrize("plan", [step_rscan, step_grid_rscan])
def test_relative_step_scans_move_relative_to_and_return_to_start(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    x_axis: Motor,
    plan,
):
    run_engine(bps.mv(x_axis, 5))

    run_engine(plan([], x_axis, -1, 1, 0.5))

    positions = [e["data"][x_axis.name] for e in run_engine_documents["event"]]
    assert positions == [4, 4.5, 5, 5.5, 6]
    assert run_engine(bps.rd(x_axis)).plan_result == 5  # type: ignore
