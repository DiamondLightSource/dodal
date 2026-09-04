import math
import re
from collections.abc import Mapping, Sequence
from typing import cast

import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
from event_model.documents import (
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
    StreamResource,
)
from ophyd_async.core import AsyncReadable, StandardDetector
from ophyd_async.sim import SimMotor
from ophyd_async.testing import assert_emitted
from pydantic import ValidationError

from dodal.plans.scans.types import (
    MovableListOfPoints,
    MovableStartStep,
    MovableStartStop,
    MovableStartStopNum,
    MovableStartStopStep,
    Number,
)
from dodal.plans.scans.wrapped import (
    count,
    list_grid_rscan,
    list_grid_scan,
    list_rscan,
    list_scan,
    num_grid_rscan,
    num_grid_scan,
    num_rscan,
    num_scan,
    step_grid_rscan,
    step_grid_scan,
    step_rscan,
    step_scan,
)


def assert_expected_shape(
    run_engine_documents: Mapping[str, list[dict]], expected_shape: tuple[int, ...]
) -> None:
    start = run_engine_documents["start"][0]
    assert start["shape"] == expected_shape


def test_count_delay_validation(det: StandardDetector, run_engine: RunEngine):
    args: dict[float | Sequence[float], str] = {  # type: ignore
        # List wrong length
        (1,): "Number of delays given must be 2: was given 1",
        (1, 2, 3): "Number of delays given must be 2: was given 3",
        # Delay non-physical
        # negative time
        -1: "Input should be greater than or equal to 0",
        (-1, 2): "Input should be greater than or equal to 0",
        # # null time
        None: "Input should be a valid number",
        (None, 2): "Input should be a valid number",
        # # NaN time
        "foo": "Input should be a valid number",
        ("foo", 2): "Input should be a valid number",
    }
    for delay, reason in args.items():
        with pytest.raises((ValidationError, AssertionError), match=reason):
            run_engine(count([det], num=3, delay=delay))


def test_count_detectors_validation(run_engine: RunEngine):
    args: dict[str, Sequence[Readable | AsyncReadable]] = {
        # No device to read
        "1 validation error for count": set(),
        # Not Readable
        "Input should be an instance of Sequence": set("foo"),  # type: ignore
    }
    for reason, dets in args.items():
        with pytest.raises(ValidationError, match=reason):
            run_engine(count(dets))


def test_count_num_validation(det: StandardDetector, run_engine: RunEngine):
    args: dict[int, str] = {
        -1: "Input should be greater than or equal to 1",
        0: "Input should be greater than or equal to 1",
        "str": "Input should be a valid integer",  # type: ignore
    }
    for num, reason in args.items():
        with pytest.raises(ValidationError, match=reason):
            run_engine(count([det], num=num))


@pytest.mark.parametrize("num, shape", ([1, (1,)], [3, (3,)]))
def test_count_plan_produces_expected_start_document(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    shape: tuple[int, ...],
):
    run_engine(count([det], num=num))
    start = run_engine_documents.get("start")
    assert start and len(start) == 1
    run_start = cast(RunStart, start[0])
    assert (hints := run_start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )
    assert_expected_shape(run_engine_documents, shape)


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_stop_document(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    stop = run_engine_documents.get("stop")
    assert stop and len(stop) == 1
    run_stop = cast(RunStop, stop[0])
    assert run_stop.get("num_events") == {"primary": length}
    assert run_stop.get("exit_status") == "success"


def test_count_plan_produces_expected_descriptor(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
):
    run_engine(count([det], num=1))
    desc = run_engine_documents.get("descriptor")
    assert desc and len(desc) == 1
    event_desc = cast(EventDescriptor, desc[0])
    object_keys = event_desc.get("object_keys")
    assert object_keys is not None and det.name in object_keys
    assert event_desc.get("name") == "primary"


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_events(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    event_docs = run_engine_documents.get("event")
    assert event_docs and len(event_docs) == length
    for i in range(len(event_docs)):
        event = cast(Event, event_docs[i])
        assert not event.get("data")  # empty data
        assert event.get("seq_num") == i + 1


@pytest.mark.parametrize("num", [1, 3])
def test_count_plan_produces_expected_resources(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
):
    run_engine(count([det], num=num))
    stream_resource_docs = run_engine_documents.get("stream_resource")
    data_keys = [det.name, f"{det.name}-sum"]
    assert stream_resource_docs and len(stream_resource_docs) == len(data_keys)
    for i in range(len(stream_resource_docs)):
        resource = cast(StreamResource, stream_resource_docs[i])
        assert resource.get("data_key") == data_keys[i]


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_datums(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    stream_datum = run_engine_documents.get("stream_datum")
    data_keys = [det.name, f"{det.name}-sum"]
    assert stream_datum and len(stream_datum) == len(data_keys) * length


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


@pytest.fixture(params=[0, 1], ids=["0 detector(s)", "1 detector(s)"])
def detectors(
    request: pytest.FixtureRequest, det: StandardDetector
) -> Sequence[StandardDetector]:
    return [] if request.param == 0 else [det]


@pytest.mark.parametrize(
    "trajectories_start_stop, num",
    [
        ([("x_axis", 0.0, 2.2)], 5),
        ([("x_axis", 1.1, -1.1)], 3),
        ([("x_axis", -1.1, 1.1), ("y_axis", 2.2, -2.2)], 5),
        ([("x_axis", 0, 1.1), ("y_axis", 2.2, 3.3)], 5),
    ],
    indirect=["trajectories_start_stop"],
)
def test_num_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop: list[MovableStartStop],
    num: int,
):
    run_engine(
        num_scan(
            detectors, trajectories_start_stop[0], *trajectories_start_stop[1:], num=num
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_num_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine,
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    with pytest.raises(ValueError):
        run_engine(num_scan([], x_axis, -1, 1, (y_axis, 1, 5, 1), num=5))  # type: ignore


@pytest.mark.parametrize(
    "trajectories_start_stop_num, snake_axes",
    [
        ([("x_axis", -1.1, 1.1, 5)], True),
        ([("x_axis", -1.1, 1.1, 5)], False),
        ([("x_axis", 0, 1.1, 5), ("y_axis", 2.2, 3.3, 5)], True),
        ([("x_axis", 0, 1.1, 5), ("y_axis", 2.2, 3.3, 5)], False),
    ],
    indirect=["trajectories_start_stop_num"],
)
def test_num_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_num: list[MovableStartStopNum],
    snake_axes: bool,
):
    run_engine(
        num_grid_scan(
            detectors,
            trajectories_start_stop_num[0],
            *trajectories_start_stop_num[1:],
            snake_axes=snake_axes,
        )
    )
    expected_shape = tuple(num for _, _, _, num in trajectories_start_stop_num)
    _assert_emitted(run_engine_documents, detectors, math.prod(expected_shape))
    assert_expected_shape(run_engine_documents, expected_shape)


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([-1.1, 1.1, 5, 2.2, -2.2, 3], [0, 1.1, 3, 2.2, 3.3, 5]),
)
def test_num_scan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    x_axis: SimMotor,
    x_start: Number,
    x_stop: Number,
    x_num: int,
    y_axis: SimMotor,
    y_start: Number,
    y_stop: Number,
    y_num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_scan(
                [],
                (x_axis, x_start, x_stop, x_num),
                (y_axis, y_start, y_stop, y_num),
                snake_axes=[x_axis],
            )
        )


@pytest.mark.parametrize(
    "trajectories_start_stop, num",
    [
        ([("x_axis", 0.0, 2.2)], 5),
        ([("x_axis", 1.1, -1.1)], 3),
        ([("x_axis", -1.1, 1.1), ("y_axis", 2.2, -2.2)], 6),
        ([("x_axis", 0, 1.1), ("y_axis", 2.2, 3.3)], 5),
    ],
    indirect=["trajectories_start_stop"],
)
def test_num_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop: list[MovableStartStop],
    num: int,
):
    run_engine(
        num_rscan(
            detectors, trajectories_start_stop[0], *trajectories_start_stop[1:], num=num
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "trajectories_start_stop_num, snake_axes",
    [
        ([("x_axis", -1.1, 1.1, 5)], True),
        ([("x_axis", 0, 1.1, 5)], False),
        ([("x_axis", -1.1, 1.1, 5), ("y_axis", 2.2, -2.2, 3)], True),
        ([("x_axis", 0, 1.1, 5), ("y_axis", 2.2, 3.3, 5)], False),
    ],
    indirect=["trajectories_start_stop_num"],
)
def test_num_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_num: list[MovableStartStopNum],
    snake_axes: bool,
):
    run_engine(
        num_grid_rscan(
            detectors,
            trajectories_start_stop_num[0],
            *trajectories_start_stop_num[1:],
            snake_axes=snake_axes,
        )
    )
    expected_shape = tuple(num for _, _, _, num in trajectories_start_stop_num)
    _assert_emitted(run_engine_documents, detectors, math.prod(expected_shape))
    assert_expected_shape(run_engine_documents, expected_shape)


def test_num_grid_rscan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_rscan(
                [], (x_axis, 1, 6, 10), (y_axis, -10, 0, 5), snake_axes=[x_axis]
            )
        )


@pytest.mark.parametrize(
    "trajectories_with_list",
    [
        [("x_axis", [0, 1, 2, 3])],
        [("x_axis", [3, 2, 1]), ("y_axis", [1, 2, 3])],
        [
            ("x_axis", [-1.1, -2.2, -3.3, -4.4, -5.5]),
            ("y_axis", [1.1, 2.2, 3.3, 4.4, 5.5]),
        ],
    ],
    indirect=True,
)
def test_list_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_with_list: list[MovableListOfPoints],
):
    num = len(trajectories_with_list[0][1])
    run_engine(
        list_scan(detectors, trajectories_with_list[0], *trajectories_with_list[1:])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_list_scan_fails_with_differnt_list_lengths(
    run_engine: RunEngine, x_axis: SimMotor, y_axis: SimMotor
):
    with pytest.raises(ValueError):
        run_engine(list_scan([], (x_axis, [1, 2, 3, 4, 5]), (y_axis, [1, 2, 3, 4])))


@pytest.mark.parametrize(
    "trajectories_with_list",
    [
        [("x_axis", [0, 1, 2, 3])],
        [("x_axis", [1.1, 2.2, 3.3])],
        [("x_axis", [3, 2, 1]), ("y_axis", [1, 2, 3])],
        [
            ("x_axis", [-1.1, -2.2, -3.3, -4.4, -5.5]),
            ("y_axis", [1.1, 2.2, 3.3, 4.4, 5.5]),
        ],
    ],
    indirect=True,
)
def test_list_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_with_list: list[MovableListOfPoints],
):
    num = len(trajectories_with_list[0][1])
    run_engine(
        list_rscan(detectors, trajectories_with_list[0], *trajectories_with_list[1:])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_list_rscan_fails_with_differnt_list_lengths(
    run_engine: RunEngine, x_axis: SimMotor, y_axis: SimMotor
):
    with pytest.raises(ValueError):
        run_engine(list_rscan([], (x_axis, [1, 2, 3, 4, 5]), (y_axis, [1, 2, 3, 4])))


@pytest.mark.parametrize(
    "trajectories_with_list",
    [
        [("x_axis", [-1.1, -2.2, -3.3, -4.4, -5.5])],
        [("x_axis", [3, 2, 1]), ("y_axis", [1, 2, 3, 4])],
    ],
    indirect=True,
)
def test_list_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_with_list: list[MovableListOfPoints],
):
    shape = tuple(len(points) for _, points in trajectories_with_list)
    num = math.prod(shape)
    run_engine(
        list_grid_scan(
            detectors, trajectories_with_list[0], *trajectories_with_list[1:]
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, shape)


@pytest.mark.parametrize(
    "trajectories_with_list",
    [
        [("x_axis", [1.1, 2.2, 3.3, 4.4, 5.5])],
        [("x_axis", [3, 2, 1]), ("y_axis", [1, 2, 3, 4])],
    ],
    indirect=True,
)
def test_list_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_with_list: list[MovableListOfPoints],
):
    shape = tuple(len(points) for _, points in trajectories_with_list)
    num = math.prod(shape)
    run_engine(
        list_grid_rscan(
            detectors, trajectories_with_list[0], *trajectories_with_list[1:]
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, shape)


@pytest.mark.parametrize(
    "trajectories_start_stop_step, trajectories_start_step, expected_num",
    [
        ([("x_axis", 0, 1, 0.25)], [], 5),
        ([("x_axis", 0, 1, 0.25)], [("y_axis", 0, 0.25)], 5),
    ],
    indirect=["trajectories_start_stop_step", "trajectories_start_step"],
)
def test_step_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_step: list[MovableStartStopStep],
    trajectories_start_step: list[MovableStartStep],
    expected_num: int,
):
    run_engine(
        step_scan(
            detectors,
            trajectories_start_stop_step[0],
            *trajectories_start_step,
        )
    )
    _assert_emitted(run_engine_documents, detectors, expected_num)
    assert_expected_shape(run_engine_documents, (expected_num,))


@pytest.mark.parametrize(
    "trajectories_start_stop_step, expected_shape, snake",
    [
        ([("x_axis", 0, 1, 0.25)], (5,), True),
        ([("x_axis", 0, 1, 0.25)], (5,), False),
        ([("x_axis", 0, 10, 2.5), ("y_axis", 0, -10, -2.5)], (5, 5), True),
        ([("x_axis", 0, 10, 2.5), ("y_axis", 0, -10, -2.5)], (5, 5), False),
    ],
    indirect=["trajectories_start_stop_step"],
)
def test_step_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_step: list[MovableStartStopStep],
    expected_shape: tuple[int, ...],
    snake: bool,
):
    run_engine(
        step_grid_scan(
            detectors,
            trajectories_start_stop_step[0],
            *trajectories_start_stop_step[1:],
            snake_axes=snake,
        )
    )
    _assert_emitted(run_engine_documents, detectors, math.prod(expected_shape))
    assert_expected_shape(run_engine_documents, expected_shape)


@pytest.mark.parametrize(
    "trajectories_start_stop_step, trajectories_start_step, expected_num",
    [
        ([("x_axis", 0, 1, 0.25)], [], 5),
        ([("x_axis", 0, 1, 0.25)], [("y_axis", 0, 0.25)], 5),
    ],
    indirect=["trajectories_start_stop_step", "trajectories_start_step"],
)
def test_step_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_step: list[MovableStartStopStep],
    trajectories_start_step: list[MovableStartStep],
    expected_num: int,
):
    run_engine(
        step_rscan(
            detectors,
            trajectories_start_stop_step[0],
            *trajectories_start_step,
        )
    )
    _assert_emitted(run_engine_documents, detectors, expected_num)
    assert_expected_shape(run_engine_documents, (expected_num,))


@pytest.mark.parametrize(
    "trajectories_start_stop_step, expected_shape, snake",
    [
        ([("x_axis", 0, 1, 0.25)], (5,), True),
        ([("x_axis", 0, 1, 0.25)], (5,), False),
        ([("x_axis", 0, 10, 2.5), ("y_axis", 0, -10, -2.5)], (5, 5), True),
        ([("x_axis", 0, 10, 2.5), ("y_axis", 0, -10, -2.5)], (5, 5), False),
    ],
    indirect=["trajectories_start_stop_step"],
)
def test_step_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    trajectories_start_stop_step: list[MovableStartStopStep],
    expected_shape: tuple[int, ...],
    snake: bool,
):
    run_engine(
        step_grid_rscan(
            detectors,
            trajectories_start_stop_step[0],
            *trajectories_start_stop_step[1:],
            snake_axes=snake,
        )
    )
    _assert_emitted(run_engine_documents, detectors, math.prod(expected_shape))
    assert_expected_shape(run_engine_documents, expected_shape)


def test_step_grid_scan_fails_when_given_wrong_number_of_args_for_first_axis(
    run_engine: RunEngine,
    x_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Trajectory must contain exactly 4 values. "
            "Expected (movable, start, stop, step). "
            "Received 3 values: ('x_axis', 1, 5)"
        ),
    ):
        run_engine(step_grid_scan([], (x_axis, 1, 5)))  # type: ignore


def test_step_grid_scan_fails_when_given_wrong_number_of_args_for_other_axis(
    run_engine: RunEngine,
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Trajectory must contain exactly 4 values. "
            "Expected (movable, start, stop, step). "
            "Received 3 values: ('y_axis', 1, 2)"
        ),
    ):
        run_engine(step_grid_scan([], (x_axis, 1, 5, 1), (y_axis, 1, 2)))  # type: ignore


def test_step_scan_fails_with_step_size_zero(
    run_engine: RunEngine,
    x_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Step size cannot be 0. "
            "Expected (movable, start, stop, step). "
            "Received (x_axis, 1, 5, 0)"
        ),
    ):
        run_engine(step_scan([], (x_axis, 1, 5, 0)))


def test_step_scan_fails_with_start_and_stop_being_same_value(
    run_engine: RunEngine,
    x_axis: SimMotor,
):
    start = stop = 0
    step = 5
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Start and stop values cannot be the same. "
            "Expected (movable, start, stop, step). "
            f"Received ({x_axis.name}, {start}, {stop}, {step})."
        ),
    ):
        run_engine(step_scan([], (x_axis, start, stop, step)))


def test_step_scan_fails_when_given_wrong_number_of_args_for_second_axes(
    run_engine: RunEngine,
    x_axis: SimMotor,
    y_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Trajectory must contain exactly 3 values. "
            "Expected (movable, start, step). "
            "Received 4 values: ('y_axis', 1, 5, 1)"
        ),
    ):
        run_engine(step_scan([], (x_axis, 0, 1, 0.1), (y_axis, 1, 5, 1)))  # type: ignore


def test_scan_fails_when_not_using_movable(
    run_engine: RunEngine,
    x_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The first value in a trajectory must implement the Movable protocol. "
            "y_axis does not implement Movable. "
            "Received ('y_axis', 1, 5, 1)."
        ),
    ):
        run_engine(step_scan([], (x_axis, 0, 1, 0.1), ("y_axis", 1, 5, 1)))  # type: ignore


def test_scan_fails_when_using_invalid_structure(
    run_engine: RunEngine,
    x_axis: SimMotor,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Trajectory  has invalid types. Expected (movable, start, stop, step). "
            "Received ('x_axis', 0, 1, [0.1])."
        ),
    ):
        run_engine(step_rscan([], (x_axis, 0, 1, [0.1])))  # type: ignore
