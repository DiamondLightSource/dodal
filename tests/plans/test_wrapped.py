from collections.abc import Sequence
from typing import Any, cast

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
    _make_args,
    _make_concurrently_stepped_lists,
    _make_independently_stepped_lists,
    _make_stepped_list,
    count,
    grid_num_rscan,
    grid_num_scan,
    list_grid_rscan,
    list_grid_scan,
    list_rscan,
    list_scan,
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
    "num_params, params", ([2, [1, 2, 3, 4]], [3, [1, 2, 3, 3, 4, 3]])
)
def test_make_args(x_axis: Motor, y_axis: Motor, num_params: int, params: list[float]):
    movers = [x_axis, y_axis]
    args = _make_args(movers=movers, params=params, num_params=num_params)
    print(args)
    assert len(args) == len(movers) + len(params)
    assert args[0] == x_axis
    assert args[(num_params + 1)] == y_axis
    assert args[1] == 1
    assert args[(num_params + 2)] == 3


def test_make_args_when_given_lists(x_axis: Motor, y_axis: Motor):
    args = _make_args(
        movers=[x_axis, y_axis], params=[[1, 2, 3, 4], [3, 4, 5, 6]], num_params=1
    )
    print(args)
    assert len(args) == 4
    assert args[0] == x_axis
    assert args[2] == y_axis
    assert args[1][0] == 1
    assert args[3][0] == 3


@pytest.mark.parametrize("x_start, x_stop, num", ([0, 2, 5], [1, -1, 3]))
def test_num_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    num: int,
):
    run_engine(
        num_scan(detectors=[det], movers=[x_axis], params=[x_start, x_stop], num=num)
    )


@pytest.mark.parametrize(
    "x_start, x_stop, y_start, y_stop, num", ([0, 2, 2, 0, 5], [-1, 1, -1, 1, 3])
)
def test_num_scan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    num: int,
):
    run_engine(
        num_scan(
            detectors=[det],
            movers=[x_axis, y_axis],
            params=[x_start, x_stop, y_start, y_stop],
            num=num,
        )
    )


def test_num_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, y_axis: Motor
):
    with pytest.raises(ValueError):
        run_engine(
            num_scan(detectors=[det], movers=[x_axis, y_axis], params=[0, 1, 2], num=3)
        )


@pytest.mark.parametrize(
    "x_start, x_stop, y_start, y_stop, num", ([-1, 1, 2, 0, 0], [-1, 1, -1, 1, 3.5])
)
def test_num_scan_fails_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_scan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[x_start, x_stop, y_start, y_stop],
                num=num,
            )
        )


@pytest.mark.parametrize("x_start, x_stop, num", ([0, 2, 5], [1, -1, 3]))
def test_num_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    num: int,
):
    run_engine(
        num_rscan(detectors=[det], movers=[x_axis], params=[x_start, x_stop], num=num)
    )


@pytest.mark.parametrize(
    "x_start, x_stop, y_start, y_stop, num", ([0, 2, 2, 0, 5], [-1, 1, -1, 1, 3])
)
def test_num_rscan_with_two_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    num: int,
):
    run_engine(
        num_rscan(
            detectors=[det],
            movers=[x_axis, y_axis],
            params=[x_start, x_stop, y_start, y_stop],
            num=num,
        )
    )


@pytest.mark.parametrize(
    "x_start, x_stop, y_start, y_stop, num", ([-1, 1, 2, 0, 0], [-1, 1, -1, 1, 3.5])
)
def test_num_rscan_fails_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_rscan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[x_start, x_stop, y_start, y_stop],
                num=num,
            )
        )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_scan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
        )
    )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_scan_when_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_scan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
            snake_axes=True,
        )
    )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_scan_when_snaking_subset_of_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_scan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
            snake_axes=[x_axis],
        )
    )


def test_grid_num_scan_fails_when_snaking_slow_axis(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            grid_num_scan(
                detectors=[det],
                movers=[y_axis, x_axis],
                params=[0, 2, 3, 0, 2, 3],
                snake_axes=[y_axis],
            )
        )


def test_grid_num_scan_fails_when_given_length_of_zero(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(RuntimeError):
        run_engine(
            grid_num_scan(
                detectors=[det],
                movers=[y_axis, x_axis],
                params=[0, 2, 0, 0, 2, 3],
            )
        )


def test_grid_num_scan_fails_when_given_non_integer_length(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(TypeError):
        run_engine(
            grid_num_scan(
                detectors=[det],
                movers=[y_axis, x_axis],
                params=[0, 2, 3.5, 0, 2, 3],
            )
        )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_rscan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
        )
    )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_rscan_when_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_rscan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
            snake_axes=True,
        )
    )


@pytest.mark.parametrize(
    "x_start, x_stop, x_num, y_start, y_stop, y_num",
    ([0, 2, 3, 0, 2, 3], [-1, 1, 5, 1, -1, 5]),
)
def test_grid_num_rscan_when_snaking_subset_of_axes(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    x_start: Any,
    x_stop: Any,
    x_num: int,
    y_axis: Motor,
    y_start: Any,
    y_stop: Any,
    y_num: int,
):
    run_engine(
        grid_num_rscan(
            detectors=[det],
            movers=[y_axis, x_axis],
            params=[y_start, y_stop, y_num, x_start, x_stop, x_num],
            snake_axes=[x_axis],
        )
    )


def test_grid_num_rscan_fails_when_snaking_slow_axis(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            grid_num_rscan(
                detectors=[det],
                movers=[y_axis, x_axis],
                params=[0, 2, 3, 0, 2, 3],
                snake_axes=[y_axis],
            )
        )


def test_grid_num_rscan_fails_when_given_length_of_zero(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(RuntimeError):
        run_engine(
            grid_num_rscan(
                detectors=[det],
                movers=[y_axis, x_axis],
                params=[0, 2, 0, 0, 2, 3],
            )
        )


def test_grid_num_rscan_fails_when_given_non_integer_length(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(TypeError):
        run_engine(
            grid_num_rscan(
                detectors=[det], movers=[y_axis, x_axis], params=[0, 2, 3.5, 0, 2, 3]
            )
        )


@pytest.mark.parametrize("x_list", ([[0, 1, 2, 3]], [[1.1, 2.2, 3.3]]))
def test_list_scan(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, x_list: Any
):
    run_engine(list_scan(detectors=[det], movers=[x_axis], params=x_list))


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
    run_engine(
        list_scan(detectors=[det], movers=[x_axis, y_axis], params=[x_list, y_list])
    )


def test_list_scan_with_two_axes_fails_when_given_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_scan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[[1, 2, 3, 4, 5], [1, 2, 3, 4]],
            )
        )


@pytest.mark.parametrize("x_list", ([[0, 1, 2, 3]], [[1.1, 2.2, 3.3]]))
def test_list_rscan(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, x_list: Any
):
    run_engine(list_rscan(detectors=[det], movers=[x_axis], params=x_list))


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
    run_engine(
        list_rscan(detectors=[det], movers=[x_axis, y_axis], params=[x_list, y_list])
    )


def test_list_rscan_with_two_axes_fails_when_given_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_rscan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[[1, 2, 3, 4, 5], [1, 2, 3, 4]],
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
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
    run_engine(
        list_grid_scan(
            detectors=[det], movers=[x_axis, y_axis], params=[x_list, y_list]
        )
    )


def test_list_grid_scan_when_given_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    run_engine(
        list_grid_scan(
            detectors=[det],
            movers=[x_axis, y_axis],
            params=[[1, 2, 3, 4, 5], [1, 2, 3, 4]],
        )
    )


def test_list_grid_scan_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(TypeError):
        run_engine(
            list_grid_scan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[[1, 2, 3, 4, 5], ["one", 2, 3, 4, 5]],
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
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
        list_grid_rscan(
            detectors=[det], movers=[x_axis, y_axis], params=[x_list, y_list]
        )
    )


def test_list_grid_rscan_with_two_axes_when_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    run_engine(
        list_grid_rscan(
            detectors=[det],
            movers=[x_axis, y_axis],
            params=[[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]],
            snake_axes=True,
        )
    )


def test_list_grid_rscan_when_given_differnt_list_lengths(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    run_engine(
        list_grid_rscan(
            detectors=[det],
            movers=[x_axis, y_axis],
            params=[[1, 2, 3, 4, 5], [1, 2, 3, 4]],
        )
    )


def test_list_grid_rscan_when_given_bad_info(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(TypeError):
        run_engine(
            list_grid_rscan(
                detectors=[det],
                movers=[x_axis, y_axis],
                params=[[1, 2, 3, 4, 5], ["one", 2, 3, 4, 5]],
            )
        )


def test_make_stepped_list_when_given_three_params():
    stepped_list = _make_stepped_list(params=[0, 1, 0.1])
    assert len(stepped_list) == 11
    assert stepped_list[0] == 0
    assert stepped_list[-1] == 1


def test_make_stepped_list_when_given_two_params():
    stepped_list = _make_stepped_list(params=[0, 0.1], num=11)
    assert len(stepped_list) == 11
    assert stepped_list[0] == 0
    assert stepped_list[-1] == 1


def test_make_concurrently_stepped_lists():
    stepped_lists = _make_concurrently_stepped_lists(
        movers_len=2, params=[0, 1, 0.1, 0, 1]
    )
    assert len(stepped_lists) == 2
    assert len(stepped_lists[0]) == 11 and len(stepped_lists[1]) == 11
    assert stepped_lists[0][-1] == 1
    assert stepped_lists[1][-1] == 10


def test_make_independently_stepped_lists():
    stepped_lists = _make_independently_stepped_lists(
        movers_len=2, params=[0, 1, 0.1, -10, 10, 1]
    )
    assert len(stepped_lists) == 2
    assert len(stepped_lists[0]) == 11 and len(stepped_lists[1]) == 21
    assert stepped_lists[0][-1] == 1
    assert stepped_lists[1][-1] == 10


@pytest.mark.parametrize("params", ([0, 1, 0.1], [-1, 1, 0.1], [0, 10, 1]))
def test_step_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    params: list[Any],
):
    run_engine(step_scan(detectors=[det], movers=[x_axis], params=params))


@pytest.mark.parametrize(
    "params", ([0, 1, 0.1, 0, 0.1], [-1, 1, 0.1, -1, 0.1], [0, 10, 1, 0, 1])
)
def test_step_scan_with_multiple_movers(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(step_scan(detectors=[det], movers=[x_axis, y_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 1, 0.1, 0]))
def test_step_scan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    with pytest.raises(ValueError):
        run_engine(step_scan(detectors=[det], movers=[x_axis, y_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1], [-1, 1, 0.1], [0, 10, 1]))
def test_step_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    params: list[Any],
):
    run_engine(step_rscan(detectors=[det], movers=[x_axis], params=params))


@pytest.mark.parametrize(
    "params", ([0, 1, 0.1, 0, 0.1], [-1, 1, 0.1, -1, 0.1], [0, 10, 1, 0, 1])
)
def test_step_rscan_with_multiple_movers(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(step_rscan(detectors=[det], movers=[x_axis, y_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 1, 0.1, 0]))
def test_step_rscan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    with pytest.raises(ValueError):
        run_engine(step_rscan(detectors=[det], movers=[x_axis, y_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 10, 1, 0, 10, 1]))
def test_step_grid_scan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(step_grid_scan(detectors=[det], movers=[y_axis, x_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 10, 1, 0, 10, 1]))
def test_step_grid_scan_when_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(
        step_grid_scan(
            detectors=[det], movers=[y_axis, x_axis], params=params, snake_axes=True
        )
    )


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1], [0, 10, 1, 0]))
def test_step_grid_scan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    with pytest.raises(ValueError):
        run_engine(
            step_grid_scan(
                detectors=[det], movers=[y_axis, x_axis], params=params, snake_axes=True
            )
        )


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 10, 1, 0, 10, 1]))
def test_step_grid_rscan(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(step_grid_rscan(detectors=[det], movers=[y_axis, x_axis], params=params))


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1, 0.1], [0, 10, 1, 0, 10, 1]))
def test_step_grid_rscan_when_snaking(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    run_engine(
        step_grid_rscan(
            detectors=[det], movers=[y_axis, x_axis], params=params, snake_axes=True
        )
    )


@pytest.mark.parametrize("params", ([0, 1, 0.1, 0, 1], [0, 10, 1, 0]))
def test_step_grid_rscan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    det: StandardDetector,
    x_axis: Motor,
    y_axis: Motor,
    params: list[Any],
):
    with pytest.raises(ValueError):
        run_engine(
            step_grid_rscan(
                detectors=[det], movers=[y_axis, x_axis], params=params, snake_axes=True
            )
        )
