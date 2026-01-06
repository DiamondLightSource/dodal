from collections.abc import Sequence
from typing import cast

import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
from event_model.documents import (
    Document,
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
    StreamResource,
)
from ophyd_async.core import (
    AsyncReadable,
    StandardDetector,
)
from pydantic import ValidationError

from dodal.devices.motors import Motor
from dodal.plans.wrapped import (
    _make_list_scan_args,
    _make_num_scan_args,
    _make_step_scan_args,
    _make_stepped_list,
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


@pytest.fixture
def documents_from_num(
    request: pytest.FixtureRequest, det: StandardDetector, run_engine: RunEngine
) -> dict[str, list[Document]]:
    docs: dict[str, list[Document]] = {}
    run_engine(
        count([det], num=request.param),
        lambda name, doc: docs.setdefault(name, []).append(doc),
    )
    return docs


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
        print(delay)


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


@pytest.mark.parametrize(
    "documents_from_num, shape", ([1, (1,)], [3, (3,)]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_start_document(
    documents_from_num: dict[str, list[Document]], shape: tuple[int, ...]
):
    docs = documents_from_num.get("start")
    assert docs and len(docs) == 1
    start = cast(RunStart, docs[0])
    assert start.get("shape") == shape
    assert (hints := start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )


@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_stop_document(
    documents_from_num: dict[str, list[Document]], length: int
):
    docs = documents_from_num.get("stop")
    assert docs and len(docs) == 1
    stop = cast(RunStop, docs[0])
    assert stop.get("num_events") == {"primary": length}
    assert stop.get("exit_status") == "success"


@pytest.mark.parametrize("documents_from_num", [1], indirect=True)
def test_plan_produces_expected_descriptor(
    documents_from_num: dict[str, list[Document]], det: StandardDetector
):
    docs = documents_from_num.get("descriptor")
    assert docs and len(docs) == 1
    descriptor = cast(EventDescriptor, docs[0])
    object_keys = descriptor.get("object_keys")
    assert object_keys is not None and det.name in object_keys
    assert descriptor.get("name") == "primary"


@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_events(
    documents_from_num: dict[str, list[Document]],
    length: int,
    det: StandardDetector,
):
    docs = documents_from_num.get("event")
    assert docs and len(docs) == length
    for i in range(len(docs)):
        event = cast(Event, docs[i])
        assert not event.get("data")  # empty data
        assert event.get("seq_num") == i + 1


@pytest.mark.parametrize("documents_from_num", [1, 3], indirect=True)
def test_plan_produces_expected_resources(
    documents_from_num: dict[str, list[Document]],
    det: StandardDetector,
):
    docs = documents_from_num.get("stream_resource")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys)
    for i in range(len(docs)):
        resource = cast(StreamResource, docs[i])
        assert resource.get("data_key") == data_keys[i]


@pytest.mark.parametrize(
    "documents_from_num, length", ([1, 1], [3, 3]), indirect=["documents_from_num"]
)
def test_plan_produces_expected_datums(
    documents_from_num: dict[str, list[Document]],
    length: int,
    det: StandardDetector,
):
    docs = documents_from_num.get("stream_datum")
    data_keys = [det.name, f"{det.name}-sum"]
    assert docs and len(docs) == len(data_keys) * length


@pytest.mark.parametrize(
    "x_list, y_list, num, final_shape, final_length",
    (
        [[0.0, 1.1], [2.2, 3.3], 3, [3], 6],
        [[0.0, 1.1, 2], [2.2, 3.3, 3], None, [2, 3], 8],
    ),
)
def test_make_num_scan_args(
    x_axis: Motor,
    y_axis: Motor,
    x_list: list[float | int],
    y_list: list[float | int],
    num: int | None,
    final_shape: list[int],
    final_length: int,
):
    args, shape = _make_num_scan_args({x_axis: x_list, y_axis: y_list}, num=num)
    assert shape == final_shape
    assert len(args) == final_length
    assert args[0] == x_axis


@pytest.mark.parametrize("x_args, num", ([[0.0, 2.2], 5], [[1.1, -1.1], 3]))
def test_num_scan_with_one_axis(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    num: int,
):
    run_engine(num_scan(detectors=[det], params={x_axis: x_args}, num=num))


@pytest.mark.parametrize(
    "x_args, y_args, num", ([[-1.1, 1.1], [2.2, -2.2], 5], [[0, 1.1], [2.2, 3.3], 5])
)
def test_num_scan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
    num: int,
):
    run_engine(
        num_scan(
            detectors=[det],
            params={x_axis: x_args, y_axis: y_args},
            num=num,
        )
    )


def test_num_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, y_axis: Motor
):
    with pytest.raises(ValueError):
        run_engine(num_scan(detectors=[det], params={x_axis: [-1, 1, 5]}, num=5))


@pytest.mark.parametrize(
    "x_args, y_args,", ([[-1, 1, 0], [2, 0]], [[-1, 1, 3.5], [-1, 1]])
)
def test_num_scan_fails_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            num_scan(
                detectors=[det],
                params={x_axis: x_args, y_axis: y_args},
            )
        )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    run_engine(
        num_grid_scan(
            detectors=[det],
            params={x_axis: x_args, y_axis: y_args},
        )
    )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_scan_when_not_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    run_engine(
        num_grid_scan(
            detectors=[det], params={x_axis: x_args, y_axis: y_args}, snake_axes=False
        )
    )


def test_num_grid_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, y_axis: Motor
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_scan(detectors=[det], params={x_axis: [0, 1.1, 2], y_axis: [1.1]})
        )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_scan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_scan(
                detectors=[det],
                params={x_axis: x_args, y_axis: y_args},
                snake_axes=[x_axis],
            )
        )


@pytest.mark.parametrize("x_args, num", ([[0.0, 2.2], 5], [[1.1, -1.1], 3]))
def test_num_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    num: int,
):
    run_engine(num_rscan(detectors=[det], params={x_axis: x_args}, num=num))


@pytest.mark.parametrize(
    "x_args, y_args, num", ([[-1.1, 1.1], [2.2, -2.2], 5], [[0, 1.1], [2.2, 3.3], 5])
)
def test_num_rscan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
    num: int,
):
    run_engine(
        num_rscan(detectors=[det], params={x_axis: x_args, y_axis: y_args}, num=num)
    )


@pytest.mark.parametrize(
    "x_args, y_args, num", ([[-1, 1], [2, 0], 0], [[-1, 1], [-1, 1], 3.5])
)
def test_num_rscan_fails_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
    num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_rscan(
                detectors=[det],
                params={x_axis: x_args, y_axis: y_args},
                num=num,
            )
        )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    run_engine(
        num_grid_rscan(
            detectors=[det],
            params={x_axis: x_args, y_axis: y_args},
        )
    )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_rscan_when_not_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    run_engine(
        num_grid_rscan(
            detectors=[det], params={x_axis: x_args, y_axis: y_args}, snake_axes=False
        )
    )


@pytest.mark.parametrize(
    "x_args, y_args", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_rscan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list[float | int],
    y_axis: Motor,
    y_args: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_rscan(
                detectors=[det],
                params={x_axis: x_args, y_axis: y_args},
                snake_axes=[x_axis],
            )
        )


@pytest.mark.parametrize(
    "x_args, y_args, grid, final_shape, final_length",
    ([[0, 1, 2], [3, 4, 5], None, [3], 4], [[0, 1, 2], [3, 4, 5, 6], True, [3, 4], 4]),
)
def test_make_list_scan_args(
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
    grid: bool,
    final_shape: list,
    final_length: int,
):
    args, shape = _make_list_scan_args(
        params={x_axis: x_args, y_axis: y_args}, grid=grid
    )
    assert len(args) == final_length
    assert shape == final_shape


def test_make_list_scan_args_fails_when_lists_are_different_lengths(
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        _make_list_scan_args(params={x_axis: [0, 1, 2], y_axis: [0, 1, 2, 3]})


@pytest.mark.parametrize("x_list", ([0, 1, 2, 3], [1.1, 2.2, 3.3]))
def test_list_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_list: list,
):
    run_engine(list_scan(detectors=[det], params={x_axis: x_list}))


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_scan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    run_engine(list_scan(detectors=[det], params={x_axis: x_list, y_axis: y_list}))


def test_list_scan_fails_with_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_scan(
                detectors=[det],
                params={x_axis: [1, 2, 3, 4, 5], y_axis: [1, 2, 3, 4]},
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3, 4]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_grid_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    run_engine(list_grid_scan(detectors=[det], params={x_axis: x_list, y_axis: y_list}))


@pytest.mark.parametrize("x_list", ([0, 1, 2, 3], [1.1, 2.2, 3.3]))
def test_list_rscan(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, x_list: list
):
    run_engine(list_rscan(detectors=[det], params={x_axis: x_list}))


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_rscan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    run_engine(list_rscan(detectors=[det], params={x_axis: x_list, y_axis: y_list}))


def test_list_rscan_fails_with_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_rscan(
                detectors=[det],
                params={x_axis: [1, 2, 3, 4, 5], y_axis: [1, 2, 3, 4]},
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3, 4]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_grid_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    run_engine(
        list_grid_rscan(detectors=[det], params={x_axis: x_list, y_axis: y_list})
    )


@pytest.mark.parametrize(
    "params",
    (
        [-1, 1, 0.1],
        [-2, 2, 0.2],
        [1, -1, -0.1],
        [2, -2, -0.2],
        [1, -1, 0.1],
        [2, -2, 0.2],
    ),
)
def test_make_stepped_list_when_given_three_params(params: list):
    stepped_list, stepped_list_length = _make_stepped_list(params=params)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


@pytest.mark.parametrize("params", ([-1, 0.1], [-2, 0.2], [1, -0.1], [2, -0.2]))
def test_make_stepped_list_when_given_two_params(params: list):
    stepped_list, stepped_list_length = _make_stepped_list(params=params, num=21)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_when_given_wrong_number_of_params():
    with pytest.raises(ValueError):
        _make_stepped_list(params=[1])


def test_make_stepped_list_when_given_step_larger_than_range():
    stepped_list, stepped_list_length = _make_stepped_list(params=[1, 2, 3])
    assert stepped_list_length == 2
    assert stepped_list == [1, 2]


def test_make_stepped_list_fails_when_given_equal_start_and_stop_values():
    with pytest.raises(ValueError):
        _make_stepped_list(params=[1.1, 1.1, 0.25])


@pytest.mark.parametrize(
    "x_args, y_args, grid, final_shape, final_length",
    (
        [[0, 1, 0.25], [0, 0.1], None, [5], 4],
        [[0, 1, 0.25], [0, 1, 0.2], True, [5, 6], 4],
        [[0, -1, -0.25], [0, -0.1], None, [5], 4],
        [[0, -1, -0.25], [0, -1, -0.2], True, [5, 6], 4],
    ),
)
def test_make_step_scan_args(
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
    grid: bool | None,
    final_shape: list,
    final_length: int,
):
    args, shape = _make_step_scan_args(
        params={x_axis: x_args, y_axis: y_args}, grid=grid
    )
    assert shape == final_shape
    assert len(args) == final_length
    assert args[0] == x_axis
    assert args[2] == y_axis


@pytest.mark.parametrize(
    "x_args, y_args, z_args, grid",
    (
        [[0, 1], [0, 0.2], [0, 0.5], None],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.2, 0.5], None],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.5], True],
        [[0, 1, 0.25], [0, 1, 0.2], [0, 0.5], True],
    ),
)
def test_make_step_scan_args_fails_when_given_incorrect_number_of_parameters(
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
    z_axis: Motor,
    z_args: list,
    grid: bool | None,
):
    with pytest.raises(ValueError):
        _make_step_scan_args(
            params={x_axis: x_args, y_axis: y_args, z_axis: z_args}, grid=grid
        )


@pytest.mark.parametrize("x_args", ([0, 1, 0.1], [-1, 1, 0.1], [0, 10, 1]))
def test_step_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
):
    run_engine(step_scan(detectors=[det], params={x_axis: x_args}))


@pytest.mark.parametrize(
    "x_args, y_args",
    ([[0, 1, 0.25], [0, 0.1]], [[-1, 1, 0.25], [-1, 0.1]], [[0, 10, 2.5], [0, 1]]),
)
def test_step_scan_with_multiple_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(step_scan(detectors=[det], params={x_axis: x_args, y_axis: y_args}))


@pytest.mark.parametrize(
    "x_args, y_args",
    (
        [[0, 1, 0.25], [0, 2, 0.5]],
        [[-1, 1, 0.25], [1, -1, -0.5]],
        [[0, 10, 2.5], [0, -10, -2.5]],
    ),
)
def test_step_grid_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(step_grid_scan(detectors=[det], params={x_axis: x_args, y_axis: y_args}))


@pytest.mark.parametrize(
    "x_args, y_args",
    (
        [[0, 1, 0.25], [0, 2, 0.5]],
        [[-1, 1, 0.25], [1, -1, -0.5]],
    ),
)
def test_step_grid_scan_when_not_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(
        step_grid_scan(
            detectors=[det], params={x_axis: x_args, y_axis: y_args}, snake_axes=False
        )
    )


@pytest.mark.parametrize(
    "x_args, y_args", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_scan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    with pytest.raises(ValueError):
        run_engine(
            step_grid_scan(detectors=[det], params={x_axis: x_args, y_axis: y_args})
        )


@pytest.mark.parametrize("x_args", ([0, 1, 0.1], [-1, 1, 0.1], [0, 10, 1]))
def test_step_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
):
    run_engine(step_rscan(detectors=[det], params={x_axis: x_args}))


@pytest.mark.parametrize(
    "x_args, y_args",
    ([[0, 1, 0.25], [0, 0.1]], [[-1, 1, 0.25], [-1, 0.1]], [[0, 10, 2.5], [0, 1]]),
)
def test_step_rscan_with_multiple_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(step_rscan(detectors=[det], params={x_axis: x_args, y_axis: y_args}))


@pytest.mark.parametrize(
    "x_args, y_args",
    (
        [[0, 1, 0.25], [0, 2, 0.5]],
        [[-1, 1, 0.25], [1, -1, -0.5]],
        [[0, 10, 2.5], [0, -10, -2.5]],
    ),
)
def test_step_grid_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(
        step_grid_rscan(detectors=[det], params={x_axis: x_args, y_axis: y_args})
    )


@pytest.mark.parametrize(
    "x_args, y_args",
    (
        [[0, 1, 0.25], [0, 2, 0.5]],
        [[-1, 1, 0.25], [1, -1, -0.5]],
    ),
)
def test_step_grid_rscan_when_not_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    run_engine(
        step_grid_rscan(
            detectors=[det], params={x_axis: x_args, y_axis: y_args}, snake_axes=False
        )
    )


@pytest.mark.parametrize(
    "x_args, y_args", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_rscan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_args: list,
    y_axis: Motor,
    y_args: list,
):
    with pytest.raises(ValueError):
        run_engine(
            step_grid_rscan(detectors=[det], params={x_axis: x_args, y_axis: y_args})
        )
